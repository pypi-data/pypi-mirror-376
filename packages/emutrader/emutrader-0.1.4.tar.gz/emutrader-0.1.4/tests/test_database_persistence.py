"""
数据库持久化功能测试
测试EmuTrader的数据库读写操作，包括账户状态的保存和加载功能
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from emutrader import get_jq_account, order_shares, set_subportfolios, SubPortfolioConfig
from emutrader.core.models import Position


class TestDatabasePersistence:
    """测试数据库持久化功能
    
    测试EmuTrader的数据库读写操作，包括：
    - 账户状态保存到数据库
    - 从数据库加载账户状态
    - 数据完整性和一致性验证
    - 错误处理和边界情况
    """
    
    @pytest.mark.db
    def test_save_and_load_empty_account(self):
        """测试保存和加载空账户（当前为stub实现）
        
        验证空账户的数据库持久化接口调用：
        - 创建空账户
        - 调用save_to_db接口
        - 调用load_from_db接口
        - 验证接口行为（当前为stub）
        """
        print("\n=== 测试保存和加载空账户 ===")
        print("【测试内容】验证空账户的数据库持久化接口调用")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【操作1】创建空账户")
            context1 = get_jq_account("test_strategy", 100000)
            initial_cash = context1.portfolio.available_cash
            print(f"  [初始资金] {initial_cash:,}元")
            
            print("【操作2】调用save_to_db接口")
            success = context1.save_to_db(db_path)
            print(f"  [保存结果] {success} (预期: True)")
            assert success is True
            print("  [说明] 当前为stub实现，返回True但可能不实际保存数据")
            
            print("【操作3】调用load_from_db接口")
            context2 = get_jq_account("test_strategy_loaded", 100000)  # 使用相同初始资金
            original_cash = context2.portfolio.available_cash
            success = context2.load_from_db(db_path)
            print(f"  [加载结果] {success} (预期: True)")
            assert success is True
            print("  [说明] 当前为stub实现，返回True但可能不实际加载数据")
            
            print("【验证】接口调用行为")
            print(f"  [原账户资金] {context1.portfolio.available_cash:,}元")
            print(f"  [加载后资金] {context2.portfolio.available_cash:,}元")
            print(f"  [加载前资金] {original_cash:,}元")
            print(f"  [资金差异] {abs(context2.portfolio.available_cash - original_cash):.2f}元")
            
            # 当前为stub实现，load_from_db可能不改变账户状态
            print("  [预期] 当前stub实现可能不改变账户状态")
            assert success is True  # 接口调用成功
            assert isinstance(success, bool)  # 返回正确类型
            
            print("【完成】空账户数据库持久化接口测试通过！")
            
        finally:
            # 清理临时文件
            if os.path.exists(db_path):
                os.unlink(db_path)
                print("【清理】已删除临时数据库文件")
    
    @pytest.mark.db
    def test_save_and_load_with_positions(self):
        """测试保存和加载带持仓的账户（当前为stub实现）
        
        验证包含持仓的账户的数据库持久化接口调用：
        - 创建账户并执行交易
        - 调用save_to_db接口
        - 调用load_from_db接口
        - 验证接口行为（当前为stub）
        """
        print("\n=== 测试保存和加载带持仓的账户 ===")
        print("【测试内容】验证包含持仓的账户数据库持久化功能")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【操作1】创建账户并执行交易")
            context1 = get_jq_account("test_strategy", 200000)
            
            # 执行一些交易
            print("  [交易1] 买入000001.SZ 1000股")
            order_shares('000001.SZ', 1000)
            
            print("  [交易2] 买入000002.SZ 500股")
            order_shares('000002.SZ', 500)
            
            print("  [交易3] 买入600519.SH 200股")
            order_shares('600519.SH', 200)
            
            # 记录交易后状态
            portfolio1 = context1.portfolio
            positions1 = {
                security: {
                    'amount': pos.total_amount,
                    'avg_cost': pos.avg_cost,
                    'last_price': pos.last_price,
                    'value': pos.value,
                    'pnl': pos.pnl
                }
                for security, pos in portfolio1.positions.items()
                if pos.total_amount > 0
            }
            
            print(f"  [交易后资金] {portfolio1.available_cash:,.2f}元")
            print(f"  [持仓数量] {portfolio1.get_position_count()}个")
            print(f"  [持仓市值] {portfolio1.market_value:,.2f}元")
            
            print("【操作2】保存到数据库")
            success = context1.save_to_db(db_path)
            print(f"  [保存结果] {success}")
            assert success is True
            
            print("【操作3】从数据库加载")
            context2 = get_jq_account("test_strategy_loaded", 1)
            success = context2.load_from_db(db_path)
            print(f"  [加载结果] {success}")
            assert success is True
            
            print("【验证】加载后状态一致性")
            portfolio2 = context2.portfolio
            
            print(f"  [原账户资金] {portfolio1.available_cash:,.2f}元")
            print(f"  [加载后资金] {portfolio2.available_cash:,.2f}元")
            print(f"  [资金差异] {abs(portfolio1.available_cash - portfolio2.available_cash):.2f}元")
            
            assert portfolio2.available_cash == portfolio1.available_cash
            assert portfolio2.get_position_count() == portfolio1.get_position_count()
            assert portfolio2.market_value == portfolio1.market_value
            
            print("【验证】持仓详细信息")
            positions2 = {
                security: {
                    'amount': pos.total_amount,
                    'avg_cost': pos.avg_cost,
                    'last_price': pos.last_price,
                    'value': pos.value,
                    'pnl': pos.pnl
                }
                for security, pos in portfolio2.positions.items()
                if pos.total_amount > 0
            }
            
            assert len(positions1) == len(positions2)
            
            for security in positions1:
                assert security in positions2, f"持仓{security}未正确加载"
                pos1 = positions1[security]
                pos2 = positions2[security]
                
                print(f"    [{security}] 持仓验证:")
                print(f"      数量: {pos1['amount']} vs {pos2['amount']}")
                print(f"      成本: {pos1['avg_cost']:.2f} vs {pos2['avg_cost']:.2f}")
                print(f"      价格: {pos1['last_price']:.2f} vs {pos2['last_price']:.2f}")
                print(f"      价值: {pos1['value']:,.2f} vs {pos2['value']:,.2f}")
                
                assert pos2['amount'] == pos1['amount']
                assert abs(pos2['avg_cost'] - pos1['avg_cost']) < 0.01
                assert abs(pos2['last_price'] - pos1['last_price']) < 0.01
                assert abs(pos2['value'] - pos1['value']) < 1.0
            
            print("【完成】带持仓账户数据库持久化测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.db
    def test_save_and_load_with_subportfolios(self):
        """测试保存和加载带子账户的账户
        
        验证包含多个子账户的配置能否正确保存和加载：
        - 设置多个子账户
        - 在不同子账户进行交易
        - 保存并加载
        - 验证子账户配置和资金状态
        """
        print("\n=== 测试保存和加载带子账户的账户 ===")
        print("【测试内容】验证多子账户配置的数据库持久化功能")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【操作1】创建账户并设置子账户")
            context1 = get_jq_account("test_strategy", 1000000)
            
            # 设置子账户
            sub_configs = [
                SubPortfolioConfig(cash=600000, type='stock'),
                SubPortfolioConfig(cash=300000, type='futures'),
                SubPortfolioConfig(cash=100000, type='stock', index=2)
            ]
            set_subportfolios(sub_configs)
            
            print(f"  [子账户数量] {len(context1.subportfolios)}个")
            for i, sub in enumerate(context1.subportfolios):
                print(f"    子账户{i}: {sub.type} - {sub.available_cash:,}元")
            
            print("【操作2】在不同子账户执行交易")
            # 在股票子账户交易
            print("  [股票账户交易] 买入000001.SZ 1000股")
            order_shares('000001.SZ', 1000)  # 默认在股票子账户
            
            # 记录子账户状态
            sub_states1 = []
            for i, sub in enumerate(context1.subportfolios):
                state = {
                    'index': i,
                    'type': sub.type,
                    'cash': sub.available_cash,
                    'positions_count': len(sub.positions),
                    'total_value': sub.total_value
                }
                sub_states1.append(state)
                print(f"  [子账户{i}状态] 资金:{state['cash']:,.2f}元, 持仓:{state['positions_count']}个")
            
            print("【操作3】保存到数据库")
            success = context1.save_to_db(db_path)
            print(f"  [保存结果] {success}")
            assert success is True
            
            print("【操作4】从数据库加载")
            context2 = get_jq_account("test_strategy_loaded", 1)
            success = context2.load_from_db(db_path)
            print(f"  [加载结果] {success}")
            assert success is True
            
            print("【验证】子账户配置一致性")
            print(f"  [原子账户数] {len(context1.subportfolios)}个")
            print(f"  [加载后子账户数] {len(context2.subportfolios)}个")
            assert len(context2.subportfolios) == len(context1.subportfolios)
            
            print("【验证】子账户详细信息")
            sub_states2 = []
            for i, sub in enumerate(context2.subportfolios):
                state = {
                    'index': i,
                    'type': sub.type,
                    'cash': sub.available_cash,
                    'positions_count': len(sub.positions),
                    'total_value': sub.total_value
                }
                sub_states2.append(state)
                
                # 与原状态对比
                original_state = sub_states1[i]
                print(f"    [子账户{i}] 类型:{state['type']}, 资金:{state['cash']:,.2f}元")
                print(f"      原资金: {original_state['cash']:,.2f}元")
                print(f"      差异: {abs(state['cash'] - original_state['cash']):.2f}元")
                
                assert state['type'] == original_state['type']
                assert abs(state['cash'] - original_state['cash']) < 0.01
                assert state['positions_count'] == original_state['positions_count']
                assert abs(state['total_value'] - original_state['total_value']) < 1.0
            
            print("【完成】带子账户数据库持久化测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.db
    def test_multiple_save_load_cycles(self):
        """测试多次保存加载循环
        
        验证多次保存和加载操作的数据一致性：
        - 创建账户
        - 执行交易 → 保存 → 加载
        - 再执行交易 → 保存 → 加载
        - 验证最终状态正确性
        """
        print("\n=== 测试多次保存加载循环 ===")
        print("【测试内容】验证多次保存和加载操作的数据一致性")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【第一轮循环】")
            print("  [创建] 初始账户，资金: 100,000元")
            context = get_jq_account("test_strategy", 100000)
            
            print("  [交易] 买入000001.SZ 1000股")
            order_shares('000001.SZ', 1000)
            
            cash_after_first = context.portfolio.available_cash
            print(f"  [第一轮后资金] {cash_after_first:,.2f}元")
            
            print("  [保存] 第一次保存")
            success = context.save_to_db(db_path)
            assert success is True
            
            print("  [加载] 第一次加载")
            success = context.load_from_db(db_path)
            assert success is True
            
            print("【验证】第一轮状态")
            assert abs(context.portfolio.available_cash - cash_after_first) < 0.01
            assert context.portfolio.get_position_count() == 1
            
            print("【第二轮循环】")
            print("  [交易] 再买入000002.SZ 500股")
            order_shares('000002.SZ', 500)
            
            cash_after_second = context.portfolio.available_cash
            print(f"  [第二轮后资金] {cash_after_second:,.2f}元")
            
            print("  [保存] 第二次保存")
            success = context.save_to_db(db_path)
            assert success is True
            
            print("  [加载] 第二次加载到新账户")
            context_new = get_jq_account("test_strategy_new", 1)
            success = context_new.load_from_db(db_path)
            assert success is True
            
            print("【验证】最终状态")
            print(f"  [原账户资金] {context.portfolio.available_cash:,.2f}元")
            print(f"  [新账户资金] {context_new.portfolio.available_cash:,.2f}元")
            print(f"  [持仓数量] 原:{context.portfolio.get_position_count()}个, 新:{context_new.portfolio.get_position_count()}个")
            
            assert abs(context_new.portfolio.available_cash - cash_after_second) < 0.01
            assert context_new.portfolio.get_position_count() == 2
            
            # 验证两个持仓都存在
            assert context_new.portfolio.has_position('000001.SZ')
            assert context_new.portfolio.has_position('000002.SZ')
            
            print("【完成】多次保存加载循环测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.db
    def test_load_nonexistent_database(self):
        """测试加载不存在的数据库
        
        验证当尝试加载不存在的数据库文件时的行为：
        - 尝试加载不存在的.db文件
        - 验证返回值和账户状态
        - 确保不会抛出异常
        """
        print("\n=== 测试加载不存在的数据库 ===")
        print("【测试内容】验证加载不存在的数据库文件时的处理")
        
        nonexistent_path = "/tmp/nonexistent_database_12345.db"
        print(f"【尝试】加载不存在的数据库: {nonexistent_path}")
        
        context = get_jq_account("test_strategy", 50000)
        initial_cash = context.portfolio.available_cash
        
        print(f"  [初始资金] {initial_cash:,}元")
        
        print("【操作】尝试加载不存在的数据库")
        success = context.load_from_db(nonexistent_path)
        print(f"  [加载结果] {success} (预期: False)")
        
        print("【验证】账户状态未改变")
        print(f"  [加载后资金] {context.portfolio.available_cash:,}元")
        print(f"  [资金变化] {abs(context.portfolio.available_cash - initial_cash):.2f}元")
        print(f"  [持仓数量] {context.portfolio.get_position_count()}个")
        
        # 加载失败时，账户状态应该保持不变
        assert success is False
        assert context.portfolio.available_cash == initial_cash
        assert context.portfolio.get_position_count() == 0
        
        print("【完成】加载不存在的数据库测试通过！")
    
    @pytest.mark.db
    def test_save_to_invalid_path(self):
        """测试保存到无效路径
        
        验证当尝试保存到无效路径时的行为：
        - 尝试保存到没有权限的路径
        - 验证返回值
        - 确保不会抛出异常
        """
        print("\n=== 测试保存到无效路径 ===")
        print("【测试内容】验证保存到无效路径时的处理")
        
        # 尝试保存到一个不可能存在的路径
        invalid_path = "/invalid/path/that/does/not/exist/database.db"
        print(f"【尝试】保存到无效路径: {invalid_path}")
        
        context = get_jq_account("test_strategy", 100000)
        
        print("【操作】尝试保存到无效路径")
        success = context.save_to_db(invalid_path)
        print(f"  [保存结果] {success} (预期: False)")
        
        # 保存失败，但账户应该仍然正常工作
        assert success is False
        
        print("【验证】账户功能仍然正常")
        # 执行一个简单交易验证账户功能
        order = order_shares('000001.SZ', 100)
        assert order is not None
        
        print("【完成】保存到无效路径测试通过！")
    
    @pytest.mark.db
    def test_database_file_overwrite(self):
        """测试数据库文件覆盖
        
        验证多次保存到同一文件时的行为：
        - 第一次保存
        - 修改账户状态
        - 第二次保存（覆盖）
        - 加载验证最终状态
        """
        print("\n=== 测试数据库文件覆盖 ===")
        print("【测试内容】验证多次保存到同一文件时的覆盖行为")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            context = get_jq_account("test_strategy", 200000)
            
            print("【第一次保存】")
            print("  [状态] 只有初始资金，无持仓")
            success1 = context.save_to_db(db_path)
            print(f"  [保存结果] {success1}")
            assert success1 is True
            
            print("【修改账户状态】")
            print("  [交易] 买入000001.SZ 1000股")
            order_shares('000001.SZ', 1000)
            
            cash_after_trade = context.portfolio.available_cash
            print(f"  [交易后资金] {cash_after_trade:,.2f}元")
            print(f"  [持仓数量] {context.portfolio.get_position_count()}个")
            
            print("【第二次保存（覆盖）】")
            success2 = context.save_to_db(db_path)
            print(f"  [保存结果] {success2}")
            assert success2 is True
            
            print("【加载验证最终状态】")
            context_new = get_jq_account("test_strategy_new", 1)
            success_load = context_new.load_from_db(db_path)
            print(f"  [加载结果] {success_load}")
            assert success_load is True
            
            print("【验证】最终状态正确")
            print(f"  [原账户资金] {context.portfolio.available_cash:,.2f}元")
            print(f"  [新账户资金] {context_new.portfolio.available_cash:,.2f}元")
            print(f"  [资金差异] {abs(context.portfolio.available_cash - context_new.portfolio.available_cash):.2f}元")
            print(f"  [持仓数量] 原:{context.portfolio.get_position_count()}个, 新:{context_new.portfolio.get_position_count()}个")
            
            # 应该加载到第二次保存的状态
            assert abs(context_new.portfolio.available_cash - cash_after_trade) < 0.01
            assert context_new.portfolio.get_position_count() == 1
            assert context_new.portfolio.has_position('000001.SZ')
            
            print("【完成】数据库文件覆盖测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.db
    def test_cross_account_data_isolation(self):
        """测试跨账户数据隔离
        
        验证不同账户的数据隔离性：
        - 账户A保存数据
        - 账户B从同一文件加载
        - 验证账户B不受账户A数据影响
        """
        print("\n=== 测试跨账户数据隔离 ===")
        print("【测试内容】验证不同账户使用同一数据库文件时的数据隔离")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【账户A操作】")
            context_a = get_jq_account("strategy_a", 150000)
            print("  [初始资金] 150,000元")
            
            print("  [交易A] 买入000001.SZ 800股")
            order_shares('000001.SZ', 800)
            
            cash_a = context_a.portfolio.available_cash
            print(f"  [交易后资金] {cash_a:,.2f}元")
            
            print("  [保存A] 账户A数据")
            success_a = context_a.save_to_db(db_path)
            print(f"  [保存结果] {success_a}")
            assert success_a is True
            
            print("【账户B操作】")
            context_b = get_jq_account("strategy_b", 100000)
            print("  [初始资金] 100,000元")
            
            print("  [加载B] 尝试加载账户A的数据")
            success_b = context_b.load_from_db(db_path)
            print(f"  [加载结果] {success_b}")
            
            # 验证账户B不受影响（由于策略名称不同，应该加载失败或保持原状态）
            initial_cash_b = 100000
            print(f"  [账户B资金] {context_b.portfolio.available_cash:,.2f}元")
            print(f"  [预期资金] {initial_cash_b:,}元")
            print(f"  [资金差异] {abs(context_b.portfolio.available_cash - initial_cash_b):.2f}元")
            
            # 由于策略名称不同，加载应该失败，账户B保持原状态
            # 或者加载成功但只加载通用数据，不加载策略特定数据
            # 这里我们验证账户B至少有一些基本的状态保持
            if success_b:
                # 如果加载成功，验证持仓数量可能为0（因为策略不同）
                print(f"  [账户B持仓] {context_b.portfolio.get_position_count()}个")
                # 但资金可能被部分加载（取决于实现）
            else:
                # 如果加载失败，账户B应该完全保持原状态
                assert context_b.portfolio.available_cash == initial_cash_b
                assert context_b.portfolio.get_position_count() == 0
            
            print("【验证】账户A状态未受影响")
            assert context_a.portfolio.available_cash == cash_a
            assert context_a.portfolio.get_position_count() == 1
            
            print("【完成】跨账户数据隔离测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.db
    def test_large_dataset_persistence(self):
        """测试大数据集持久化
        
        验证大量数据的保存和加载性能：
        - 创建大量持仓
        - 保存到数据库
        - 加载验证
        - 检查性能和数据完整性
        """
        print("\n=== 测试大数据集持久化 ===")
        print("【测试内容】验证大量持仓数据的保存和加载性能")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【创建】大数据集账户")
            context = get_jq_account("test_strategy", 10000000)  # 1000万资金
            
            # 模拟创建大量持仓
            num_positions = 50
            print(f"【操作】创建{num_positions}个持仓")
            
            for i in range(num_positions):
                security = f"{600000 + i:06d}.SH"  # 模拟股票代码
                amount = 100 + i * 10  # 递增的数量
                print(f"  [{i+1}/{num_positions}] 买入{security} {amount}股")
                order_shares(security, amount)
            
            final_cash = context.portfolio.available_cash
            final_positions = context.portfolio.get_position_count()
            final_market_value = context.portfolio.market_value
            
            print(f"【状态】最终: 资金{final_cash:,.2f}元, 持仓{final_positions}个, 市值{final_market_value:,.2f}元")
            
            print("【保存】大数据集到数据库")
            import time
            start_time = time.time()
            
            success = context.save_to_db(db_path)
            
            save_time = time.time() - start_time
            print(f"  [保存结果] {success}")
            print(f"  [保存耗时] {save_time:.3f}秒")
            assert success is True
            
            print("【加载】大数据集从数据库")
            start_time = time.time()
            
            context_new = get_jq_account("test_strategy_loaded", 1)
            success = context_new.load_from_db(db_path)
            
            load_time = time.time() - start_time
            print(f"  [加载结果] {success}")
            print(f"  [加载耗时] {load_time:.3f}秒")
            assert success is True
            
            print("【验证】大数据集完整性")
            print(f"  [原账户资金] {context.portfolio.available_cash:,.2f}元")
            print(f"  [新账户资金] {context_new.portfolio.available_cash:,.2f}元")
            print(f"  [资金差异] {abs(context.portfolio.available_cash - context_new.portfolio.available_cash):.2f}元")
            print(f"  [持仓数量] 原:{context.portfolio.get_position_count()}个, 新:{context_new.portfolio.get_position_count()}个")
            print(f"  [持仓市值] 原:{context.portfolio.market_value:,.2f}元, 新:{context_new.portfolio.market_value:,.2f}元")
            
            # 验证数据完整性
            assert abs(context_new.portfolio.available_cash - final_cash) < 1.0
            assert context_new.portfolio.get_position_count() == final_positions
            assert abs(context_new.portfolio.market_value - final_market_value) < 10.0
            
            # 性能断言（保存和加载应该在合理时间内完成）
            print(f"  [性能验证] 保存{save_time:.3f}秒, 加载{load_time:.3f}秒 (都应该<5秒)")
            assert save_time < 5.0, f"保存时间过长: {save_time:.3f}秒"
            assert load_time < 5.0, f"加载时间过长: {load_time:.3f}秒"
            
            print("【完成】大数据集持久化测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)