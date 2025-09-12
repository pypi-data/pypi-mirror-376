"""
QSM集成接口测试

测试EmuTrader为QSM策略系统提供的接口：
- 价格更新接口：update_market_price, batch_update_prices
- 交易执行接口：execute_trade  
- 数据持久化接口：load_from_db, save_to_db
- 持仓获取接口：get_all_securities
"""

import pytest
from datetime import datetime
from emutrader import get_jq_account, set_subportfolios, SubPortfolioConfig
from emutrader.core.trader import EmuTrader


class TestQSMPriceUpdates:
    """测试QSM价格更新接口"""
    
    def test_update_market_price_basic(self):
        """测试单个证券价格更新"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 先创建一些持仓
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        
        # 更新价格
        emutrader.update_market_price('000001.SZ', 12.0)
        
        # 验证持仓价值更新
        position = emutrader.portfolio.get_position('000001.SZ')
        assert position.last_price == 12.0
        assert position.value == 1000 * 12.0  # 12000
        
        # 验证总资产更新
        expected_total = 90000 + 12000  # cash + market_value
        assert abs(emutrader.portfolio.total_value - expected_total) < 0.01
    
    def test_update_market_price_with_timestamp(self):
        """测试带时间戳的价格更新"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        
        # 带时间戳更新价格
        test_time = datetime(2024, 3, 15, 14, 30, 0)
        emutrader.update_market_price('000001.SZ', 11.5, test_time)
        
        position = emutrader.portfolio.get_position('000001.SZ')
        assert position.last_price == 11.5
        assert position.value == 11500
    
    def test_batch_update_prices(self):
        """测试批量价格更新"""
        emutrader = get_jq_account("qsm_test", 200000, "STOCK")
        
        # 创建多个持仓
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        emutrader.execute_trade('000002.SZ', 500, 20.0)
        emutrader.execute_trade('600519.SH', 200, 50.0)
        
        # 批量更新价格
        price_data = {
            '000001.SZ': 12.0,
            '000002.SZ': 25.0,
            '600519.SH': 55.0
        }
        emutrader.batch_update_prices(price_data)
        
        # 验证所有持仓价格都更新了
        pos1 = emutrader.portfolio.get_position('000001.SZ')
        pos2 = emutrader.portfolio.get_position('000002.SZ')
        pos3 = emutrader.portfolio.get_position('600519.SH')
        
        assert pos1.last_price == 12.0
        assert pos2.last_price == 25.0  
        assert pos3.last_price == 55.0
        
        # 验证总市值
        expected_market_value = 1000*12.0 + 500*25.0 + 200*55.0  # 36000
        assert abs(emutrader.portfolio.market_value - expected_market_value) < 0.01
    
    def test_update_price_with_subportfolios(self):
        """测试子账户的价格更新"""
        emutrader = get_jq_account("qsm_test", 500000, "STOCK")
        
        # 设置子账户
        set_subportfolios([
            SubPortfolioConfig(cash=300000, type='stock'),
            SubPortfolioConfig(cash=200000, type='stock'),
        ])
        
        # 在不同子账户中创建持仓
        emutrader.execute_trade('000001.SZ', 1000, 10.0, subportfolio_index=0)
        emutrader.execute_trade('000002.SZ', 500, 20.0, subportfolio_index=1)
        
        # 更新价格
        emutrader.update_market_price('000001.SZ', 15.0)
        emutrader.update_market_price('000002.SZ', 30.0)
        
        # 验证子账户价格都更新了
        sub0_pos = emutrader.subportfolios[0].get_position('000001.SZ')
        sub1_pos = emutrader.subportfolios[1].get_position('000002.SZ')
        
        assert sub0_pos.last_price == 15.0
        assert sub1_pos.last_price == 30.0


class TestQSMTradeExecution:
    """测试QSM交易执行接口"""
    
    def test_execute_trade_buy_basic(self):
        """测试基础买入交易"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 执行买入
        success = emutrader.execute_trade('000001.SZ', 1000, 10.0)
        assert success is True
        
        # 验证持仓和资金
        position = emutrader.portfolio.get_position('000001.SZ')
        assert position.total_amount == 1000
        assert position.avg_cost == 10.0
        
        assert emutrader.portfolio.available_cash == 90000  # 100000 - 10000
        assert emutrader.portfolio.market_value == 10000
    
    def test_execute_trade_sell_basic(self):
        """测试基础卖出交易"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 先买入
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        
        # 再卖出一部分
        success = emutrader.execute_trade('000001.SZ', -500, 12.0)
        assert success is True
        
        # 验证持仓和资金
        position = emutrader.portfolio.get_position('000001.SZ')
        assert position.total_amount == 500  # 1000 - 500
        
        expected_cash = 90000 + 500 * 12.0  # 原现金 + 卖出所得
        assert emutrader.portfolio.available_cash == expected_cash
    
    def test_execute_trade_insufficient_cash(self):
        """测试资金不足的情况"""
        emutrader = get_jq_account("qsm_test", 10000, "STOCK")  # 只有1万资金
        
        # 尝试买入超过资金的股票
        success = emutrader.execute_trade('000001.SZ', 1000, 20.0)  # 需要2万
        assert success is False
        
        # 验证账户状态没有变化
        assert emutrader.portfolio.available_cash == 10000
        assert len(emutrader.portfolio.positions) == 0
    
    def test_execute_trade_insufficient_position(self):
        """测试持仓不足的情况"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 买入1000股
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        
        # 尝试卖出1500股（超过持仓）
        success = emutrader.execute_trade('000001.SZ', -1500, 12.0)
        assert success is False
        
        # 验证持仓没有变化
        position = emutrader.portfolio.get_position('000001.SZ')
        assert position.total_amount == 1000
    
    def test_execute_trade_with_subportfolio(self):
        """测试在子账户中执行交易"""
        emutrader = get_jq_account("qsm_test", 300000, "STOCK")
        
        # 设置子账户
        set_subportfolios([
            SubPortfolioConfig(cash=200000, type='stock'),
            SubPortfolioConfig(cash=100000, type='stock'),
        ])
        
        # 在第一个子账户中交易
        success = emutrader.execute_trade('000001.SZ', 1000, 15.0, subportfolio_index=0)
        assert success is True
        
        # 验证子账户状态
        sub0 = emutrader.subportfolios[0]
        position = sub0.get_position('000001.SZ')
        assert position.total_amount == 1000
        assert sub0.available_cash == 185000  # 200000 - 15000
        
        # 验证其他子账户未受影响
        sub1 = emutrader.subportfolios[1]
        assert sub1.available_cash == 100000
    
    def test_execute_trade_zero_amount(self):
        """测试零数量交易"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 零数量交易应该返回True但不执行任何操作
        success = emutrader.execute_trade('000001.SZ', 0, 10.0)
        assert success is True
        
        # 验证账户状态没有变化
        assert emutrader.portfolio.available_cash == 100000
        assert len(emutrader.portfolio.positions) == 0


class TestQSMDataPersistence:
    """测试QSM数据持久化接口"""
    
    def test_save_to_db_basic(self):
        """测试基础保存功能"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 创建一些交易
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        emutrader.execute_trade('000002.SZ', 500, 20.0)
        
        # 保存到数据库（当前是模拟实现）
        success = emutrader.save_to_db()
        assert success is True
    
    def test_save_to_db_with_path(self):
        """测试指定路径保存"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 保存到指定路径
        success = emutrader.save_to_db("test_account.db")
        assert success is True
    
    def test_load_from_db_basic(self):
        """测试基础加载功能"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 从数据库加载（当前是模拟实现）
        success = emutrader.load_from_db("test_account.db")
        assert success is True


class TestQSMSecurityManagement:
    """测试QSM证券管理接口"""
    
    def test_get_all_securities_empty(self):
        """测试获取空持仓列表"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        securities = emutrader.get_all_securities()
        assert securities == []
    
    def test_get_all_securities_with_positions(self):
        """测试获取有持仓的证券列表"""
        emutrader = get_jq_account("qsm_test", 200000, "STOCK")
        
        # 创建多个持仓
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        emutrader.execute_trade('000002.SZ', 500, 20.0)
        emutrader.execute_trade('600519.SH', 200, 50.0)
        
        securities = emutrader.get_all_securities()
        expected_securities = {'000001.SZ', '000002.SZ', '600519.SH'}
        assert set(securities) == expected_securities
    
    def test_get_all_securities_with_subportfolios(self):
        """测试从子账户获取证券列表"""
        emutrader = get_jq_account("qsm_test", 400000, "STOCK")
        
        # 设置子账户
        set_subportfolios([
            SubPortfolioConfig(cash=200000, type='stock'),
            SubPortfolioConfig(cash=200000, type='stock'),
        ])
        
        # 在不同子账户中创建持仓
        emutrader.execute_trade('000001.SZ', 1000, 10.0, subportfolio_index=0)
        emutrader.execute_trade('000002.SZ', 500, 20.0, subportfolio_index=1)
        emutrader.execute_trade('600519.SH', 200, 50.0, subportfolio_index=0)
        
        securities = emutrader.get_all_securities()
        expected_securities = {'000001.SZ', '000002.SZ', '600519.SH'}
        assert set(securities) == expected_securities
    
    def test_get_all_securities_after_sell(self):
        """测试卖出后的证券列表"""
        emutrader = get_jq_account("qsm_test", 100000, "STOCK")
        
        # 买入后再全部卖出
        emutrader.execute_trade('000001.SZ', 1000, 10.0)
        emutrader.execute_trade('000001.SZ', -1000, 12.0)
        
        securities = emutrader.get_all_securities()
        # 全部卖出后应该没有持仓了
        assert len(securities) == 0 or '000001.SZ' not in securities


class TestQSMIntegrationWorkflow:
    """测试QSM完整集成工作流程"""
    
    def test_complete_qsm_workflow(self):
        """测试完整的QSM集成工作流程"""
        # 1. 初始化EmuTrader
        emutrader = get_jq_account("qsm_strategy", 1000000, "STOCK")
        
        # 2. 设置多个子账户
        set_subportfolios([
            SubPortfolioConfig(cash=600000, type='stock'),
            SubPortfolioConfig(cash=400000, type='stock'),
        ])
        
        # 3. QSM执行交易
        securities_to_buy = [
            ('000001.SZ', 2000, 15.0, 0),  # 在子账户0中买入
            ('000002.SZ', 1000, 25.0, 1),  # 在子账户1中买入
            ('600519.SH', 400, 80.0, 0),   # 在子账户0中买入
        ]
        
        for security, amount, price, sub_index in securities_to_buy:
            success = emutrader.execute_trade(security, amount, price, sub_index)
            assert success is True
        
        # 4. QSM获取持仓证券列表用于行情订阅
        all_securities = emutrader.get_all_securities()
        assert len(all_securities) == 3
        assert set(all_securities) == {'000001.SZ', '000002.SZ', '600519.SH'}
        
        # 5. QSM接收行情并批量更新价格
        market_prices = {
            '000001.SZ': 18.0,  # 上涨
            '000002.SZ': 23.0,  # 下跌
            '600519.SH': 85.0,  # 上涨
        }
        emutrader.batch_update_prices(market_prices)
        
        # 6. 验证实时盈亏计算
        portfolio = emutrader.portfolio
        
        # 计算期望的市值和盈亏
        expected_market_value = (2000*18.0 + 1000*23.0 + 400*85.0)  # 93000
        expected_pnl = (2000*(18.0-15.0) + 1000*(23.0-25.0) + 400*(85.0-80.0))  # 6000-2000+2000 = 6000
        
        assert abs(portfolio.market_value - expected_market_value) < 0.01
        assert abs(portfolio.pnl - expected_pnl) < 0.01
        
        # 7. QSM保存账户状态
        success = emutrader.save_to_db()
        assert success is True
        
        # 8. 验证总资产 = 剩余现金 + 持仓市值
        expected_total = portfolio.available_cash + portfolio.market_value
        assert abs(portfolio.total_value - expected_total) < 0.01