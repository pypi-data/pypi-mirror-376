# -*- coding: utf-8 -*-
"""
SQLite存储实现
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseStorage
from ..core.models import AccountState, Position
from ..exceptions import StorageException


class SQLiteStorage(BaseStorage):
    """SQLite存储实现"""
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
        self.initialize()
    
    def initialize(self):
        """初始化SQLite数据库"""
        try:
            self._connection = sqlite3.connect(str(self.db_path))
            self._create_tables()
        except Exception as e:
            raise StorageException(f"初始化SQLite失败: {e}")
    
    def _create_tables(self):
        """创建数据表 - 支持多子账户架构"""
        cursor = self._connection.cursor()
        
        # 账户状态表 - 支持多子账户 (兼容聚宽子账户系统)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_states (
                strategy_name TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                account_type TEXT NOT NULL DEFAULT 'STOCK',
                account_name TEXT DEFAULT '',
                total_value REAL NOT NULL,
                available_cash REAL NOT NULL,
                transferable_cash REAL NOT NULL,
                frozen_cash REAL DEFAULT 0,
                positions_value REAL DEFAULT 0,
                
                -- 期货账户专用字段
                total_margin REAL DEFAULT 0,
                frozen_margin REAL DEFAULT 0,
                available_margin REAL DEFAULT 0,
                float_pnl REAL DEFAULT 0,
                close_pnl REAL DEFAULT 0,
                risk_ratio REAL DEFAULT 0,
                
                -- 融资融券专用字段
                total_liability REAL DEFAULT 0,
                cash_liability REAL DEFAULT 0,
                stock_liability REAL DEFAULT 0,
                maintenance_ratio REAL DEFAULT 0,
                
                -- 期权账户专用字段
                option_value REAL DEFAULT 0,
                option_margin REAL DEFAULT 0,
                
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_name, account_id),
                CHECK (account_type IN ('STOCK', 'FUTURE', 'CREDIT', 'OPTION', 'CRYPTO'))
            )
        ''')
        
        # 持仓表 - 关联到特定账户，支持多种资产类型
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                strategy_name TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                security TEXT NOT NULL,
                total_amount INTEGER DEFAULT 0,
                closeable_amount INTEGER DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                current_price REAL DEFAULT 0,
                value REAL DEFAULT 0,
                acc_avg_cost REAL DEFAULT 0,
                hold_cost REAL DEFAULT 0,
                pnl REAL DEFAULT 0,
                pnl_ratio REAL DEFAULT 0,
                
                -- 期货持仓专用字段
                direction TEXT DEFAULT 'long',
                margin REAL DEFAULT 0,
                margin_rate REAL DEFAULT 0.1,
                contract_multiplier INTEGER DEFAULT 1,
                settlement_price REAL DEFAULT 0,
                yesterday_settlement REAL DEFAULT 0,
                today_amount INTEGER DEFAULT 0,
                frozen_amount INTEGER DEFAULT 0,
                float_pnl REAL DEFAULT 0,
                
                -- 融资融券专用字段
                borrowed_amount INTEGER DEFAULT 0,
                borrowed_value REAL DEFAULT 0,
                
                -- 期权专用字段
                option_type TEXT DEFAULT '',
                strike_price REAL DEFAULT 0,
                expiry_date DATE,
                
                -- 数字货币专用字段
                staking_amount REAL DEFAULT 0,
                staking_reward REAL DEFAULT 0,
                
                asset_type TEXT DEFAULT 'STOCK',
                init_time TIMESTAMP,
                transact_time TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_name, account_id, security),
                CHECK (direction IN ('long', 'short')),
                CHECK (asset_type IN ('STOCK', 'FUTURE', 'OPTION', 'CRYPTO', 'BOND'))
            )
        ''')
        
        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                order_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                security TEXT NOT NULL,
                amount INTEGER NOT NULL,
                price REAL NOT NULL,
                order_type TEXT NOT NULL,
                commission REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                status TEXT DEFAULT 'filled',
                total_value REAL,
                net_value REAL,
                action_type TEXT DEFAULT 'open_long',
                offset_flag TEXT DEFAULT 'open',
                margin_change REAL DEFAULT 0,
                transaction_type TEXT DEFAULT 'STOCK',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filled_at TIMESTAMP
            )
        ''')
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                security TEXT NOT NULL,
                amount INTEGER NOT NULL,
                price REAL,
                style TEXT,
                status TEXT DEFAULT 'new',
                filled INTEGER DEFAULT 0,
                commission REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT DEFAULT 'open_long',
                offset_flag TEXT DEFAULT 'open',
                margin_rate REAL DEFAULT 0.1,
                contract_multiplier INTEGER DEFAULT 1,
                order_type TEXT DEFAULT 'STOCK'
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_strategy_type ON account_states(strategy_name, account_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(strategy_name, account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(strategy_name, account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(strategy_name, account_id)')
        
        self._connection.commit()
    
    def save_account_state(self, strategy_name, account_id, account_state, account_type='STOCK'):
        """保存账户状态"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO account_states 
                (strategy_name, account_id, account_type, total_value, available_cash, 
                 positions_value, frozen_cash, transferable_cash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                strategy_name,
                account_id,
                account_type,
                account_state.total_value,
                account_state.available_cash,
                account_state.positions_value,
                account_state.frozen_cash,
                account_state.transferable_cash
            ))
            self._connection.commit()
        except Exception as e:
            raise StorageException(f"保存账户状态失败: {e}")
    
    def load_account_state(self, strategy_name, account_id):
        """加载账户状态"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                'SELECT * FROM account_states WHERE strategy_name = ? AND account_id = ?', 
                (strategy_name, account_id)
            )
            row = cursor.fetchone()
            
            if row:
                from datetime import datetime
                return AccountState(
                    total_value=row[4],  # total_value
                    available_cash=row[5],  # available_cash
                    positions_value=row[8],  # positions_value
                    frozen_cash=row[7],  # frozen_cash
                    transferable_cash=row[6]  # transferable_cash
                )
            return None
        except Exception as e:
            raise StorageException(f"加载账户状态失败: {e}")
    
    def save_position(self, strategy_name, account_id, security, position):
        """保存持仓信息"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO positions 
                (strategy_name, account_id, security, total_amount, avg_cost, current_price, 
                 closeable_amount, value, acc_avg_cost, hold_cost, pnl, pnl_ratio,
                 direction, asset_type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                strategy_name,
                account_id,
                security,
                position.total_amount,
                position.avg_cost,
                position.current_price,
                position.closeable_amount,
                getattr(position, 'value', position.total_amount * position.current_price),
                getattr(position, 'acc_avg_cost', position.avg_cost),
                getattr(position, 'hold_cost', position.avg_cost),
                getattr(position, 'pnl', 0.0),
                getattr(position, 'pnl_ratio', 0.0),
                getattr(position, 'direction', 'long'),
                getattr(position, 'asset_type', 'STOCK')
            ))
            self._connection.commit()
        except Exception as e:
            raise StorageException(f"保存持仓失败: {e}")
            
    def save_positions(self, strategy_name, account_id, positions):
        """批量保存持仓信息"""
        try:
            cursor = self._connection.cursor()
            
            # 先清空该账户的持仓
            cursor.execute(
                'DELETE FROM positions WHERE strategy_name = ? AND account_id = ?',
                (strategy_name, account_id)
            )
            
            # 批量插入新持仓
            for security, position in positions.items():
                if position.total_amount > 0:
                    cursor.execute('''
                        INSERT INTO positions 
                        (strategy_name, account_id, security, total_amount, avg_cost, current_price, 
                         closeable_amount, value, acc_avg_cost, hold_cost, pnl, pnl_ratio,
                         direction, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        strategy_name,
                        account_id,
                        security,
                        position.total_amount,
                        position.avg_cost,
                        position.current_price,
                        position.closeable_amount,
                        getattr(position, 'value', position.total_amount * position.current_price),
                        getattr(position, 'acc_avg_cost', position.avg_cost),
                        getattr(position, 'hold_cost', position.avg_cost),
                        getattr(position, 'pnl', 0.0),
                        getattr(position, 'pnl_ratio', 0.0),
                        getattr(position, 'direction', 'long'),
                        getattr(position, 'asset_type', 'STOCK')
                    ))
            
            self._connection.commit()
        except Exception as e:
            raise StorageException(f"批量保存持仓失败: {e}")
    
    def load_positions(self, strategy_name, account_id):
        """加载所有持仓"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                'SELECT * FROM positions WHERE strategy_name = ? AND account_id = ?', 
                (strategy_name, account_id)
            )
            rows = cursor.fetchall()
            
            positions = {}
            for row in rows:
                security = row[2]  # security 字段位置
                positions[security] = Position(
                    security=security,
                    total_amount=row[3],  # total_amount
                    avg_cost=row[5],      # avg_cost  
                    current_price=row[6], # current_price
                    closeable_amount=row[4] # closeable_amount
                )
            
            return positions
        except Exception as e:
            raise StorageException(f"加载持仓失败: {e}")
    
    def save_transaction(self, strategy_name, account_id, transaction):
        """保存交易记录"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO transactions 
                (order_id, strategy_name, account_id, security, amount, price, 
                 order_type, commission, tax, status, total_value, net_value,
                 action_type, offset_flag, margin_change, transaction_type, filled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                transaction.order_id,
                strategy_name,
                account_id,
                transaction.security,
                transaction.amount,
                transaction.price,
                getattr(transaction, 'order_type', 'market'),
                getattr(transaction, 'commission', 0.0),
                getattr(transaction, 'tax', 0.0),
                getattr(transaction, 'status', 'filled'),
                getattr(transaction, 'total_value', transaction.amount * transaction.price),
                getattr(transaction, 'net_value', transaction.amount * transaction.price),
                getattr(transaction, 'action_type', 'open_long'),
                getattr(transaction, 'offset_flag', 'open'),
                getattr(transaction, 'margin_change', 0.0),
                getattr(transaction, 'transaction_type', 'STOCK')
            ))
            self._connection.commit()
        except Exception as e:
            raise StorageException(f"保存交易记录失败: {e}")
    
    def load_transactions(self, strategy_name, account_id, limit=100):
        """加载交易记录"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE strategy_name = ? AND account_id = ? 
                ORDER BY created_at DESC LIMIT ?
            ''', (strategy_name, account_id, limit))
            return cursor.fetchall()
        except Exception as e:
            raise StorageException(f"加载交易记录失败: {e}")
    
    def save_order(self, strategy_name, account_id, order):
        """保存订单"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO orders 
                (order_id, strategy_name, account_id, security, amount, price, 
                 style, status, filled, commission, tax, action, offset_flag,
                 margin_rate, contract_multiplier, order_type, updated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                order.order_id,
                strategy_name,
                account_id,
                order.security,
                order.amount,
                getattr(order, 'price', None),
                getattr(order, 'style', 'market'),
                getattr(order, 'status', 'new'),
                getattr(order, 'filled', 0),
                getattr(order, 'commission', 0.0),
                getattr(order, 'tax', 0.0),
                getattr(order, 'action', 'open_long'),
                getattr(order, 'offset_flag', 'open'),
                getattr(order, 'margin_rate', 0.1),
                getattr(order, 'contract_multiplier', 1),
                getattr(order, 'order_type', 'STOCK')
            ))
            self._connection.commit()
        except Exception as e:
            raise StorageException(f"保存订单失败: {e}")
    
    def load_orders(self, strategy_name, account_id, status=None):
        """加载订单"""
        try:
            cursor = self._connection.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM orders 
                    WHERE strategy_name = ? AND account_id = ? AND status = ?
                    ORDER BY created_time DESC
                ''', (strategy_name, account_id, status))
            else:
                cursor.execute('''
                    SELECT * FROM orders 
                    WHERE strategy_name = ? AND account_id = ?
                    ORDER BY created_time DESC
                ''', (strategy_name, account_id))
            return cursor.fetchall()
        except Exception as e:
            raise StorageException(f"加载订单失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None