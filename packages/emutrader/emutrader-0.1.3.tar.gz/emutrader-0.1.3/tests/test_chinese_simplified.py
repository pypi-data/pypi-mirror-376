"""
简化中文测试用例
演示在pytest中正确使用中文的方法
"""

import pytest
from emutrader import (
    get_jq_account, order_shares, order_value, order_target_percent,
    set_subportfolios, SubPortfolioConfig, transfer_cash
)


class TestChineseUsage:
    """中文使用方式测试类"""
    
    def test_basic_strategy_creation(self):
        """测试基础策略创建"""
        # 使用中文变量名
        策略名称 = "基础策略"
        初始资金 = 100000.0
        
        # 创建策略上下文
        context = get_jq_account(策略名称, 初始资金)
        
        # 验证策略属性
        assert context.run_params['strategy_name'] == 策略名称
        assert context.portfolio.total_value == 初始资金
        
        print(f"✓ 策略创建成功: {策略名称}")
    
    def test_stock_trading(self):
        """测试股票交易"""
        # 创建交易策略
        context = get_jq_account("股票交易", 200000)
        
        # 定义股票池
        股票代码 = '000001.SZ'
        股票名称 = '平安银行'
        买入数量 = 1000
        
        # 执行买入
        订单 = order_shares(股票代码, 买入数量)
        
        # 验证交易结果
        assert 订单 is not None
        assert 订单.amount == 买入数量
        
        print(f"✓ 买入成功: {股票名称} {买入数量}股")
    
    def test_portfolio_analysis(self):
        """测试投资组合分析"""
        # 创建投资组合
        context = get_jq_account("组合分析", 300000)
        
        # 执行建仓
        股票池 = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A',
            '600519.SH': '贵州茅台'
        }
        
        # 等权重建仓
        for 代码, 名称 in 股票池.items():
            order_target_percent(代码, 0.25)  # 每只25%
            
        # 分析组合状态
        组合 = context.portfolio
        持仓数量 = len([p for p in 组合.positions.values() if p.total_amount > 0])
        
        assert 持仓数量 >= 2
        assert 组合.market_value > 0
        
        print(f"✓ 组合建仓完成，持有{持仓数量}只股票")
    
    def test_subportfolio_setup(self):
        """测试子账户设置"""
        from emutrader.api import set_current_context
        
        # 创建多账户策略
        context = get_jq_account("多账户策略", 500000)
        set_current_context(context)
        
        # 配置子账户
        子账户列表 = [
            SubPortfolioConfig(cash=300000, type='stock'),
            SubPortfolioConfig(cash=200000, type='futures')
        ]
        
        set_subportfolios(子账户列表)
        
        # 验证设置结果
        assert len(context.subportfolios) == 2
        assert context.subportfolios[0].available_cash == 300000
        assert context.subportfolios[1].available_cash == 200000
        
        print("✓ 子账户设置成功")
    
    def test_cash_transfer(self):
        """测试资金转移"""
        from emutrader.api import set_current_context
        
        # 设置账户
        context = get_jq_account("资金转移测试", 400000)
        set_current_context(context)
        
        配置 = [
            SubPortfolioConfig(cash=200000, type='stock'),
            SubPortfolioConfig(cash=200000, type='futures')
        ]
        set_subportfolios(配置)
        
        # 执行资金转移
        转移金额 = 50000
        转移结果 = transfer_cash(from_pindex=1, to_pindex=0, cash=转移金额)
        
        # 验证转移结果
        assert 转移结果 is True
        assert context.subportfolios[0].available_cash == 250000  # 200000 + 50000
        assert context.subportfolios[1].available_cash == 150000  # 200000 - 50000
        
        print(f"✓ 资金转移成功: {转移金额:,}元")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 创建小资金账户
        context = get_jq_account("错误测试", 1000)
        
        try:
            # 尝试买入超过资金的股票
            order_value('000001.SZ', 100000)  # 10万元，但只有1000元
            assert False, "应该抛出异常"
        except Exception as 错误:
            错误信息 = str(错误)
            print(f"✓ 正确捕获错误: {错误信息}")
        
        # 验证账户未受影响
        assert context.portfolio.available_cash == 1000


class TestChineseDocumentation:
    """中文文档化测试"""
    
    def test_strategy_workflow(self):
        """完整策略工作流程演示"""
        print("\n=== 完整策略工作流程 ===")
        
        # 第1步: 初始化策略
        策略上下文 = get_jq_account("演示策略", 1000000)
        print(f"1. 策略初始化完成，资金: {策略上下文.portfolio.total_value:,.0f}元")
        
        # 第2步: 设置股票池
        核心股票池 = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A',
            '600519.SH': '贵州茅台',
            '000858.SZ': '五粮液'
        }
        print(f"2. 股票池设置完成，包含{len(核心股票池)}只股票")
        
        # 第3步: 执行建仓
        print("3. 开始建仓:")
        等权重比例 = 0.8 / len(核心股票池)  # 80%资金等权重
        
        for 代码, 名称 in 核心股票池.items():
            order_target_percent(代码, 等权重比例)
            print(f"   {名称}({代码}): 目标权重 {等权重比例:.1%}")
        
        # 第4步: 分析结果
        最终组合 = 策略上下文.portfolio
        持仓品种数 = len([p for p in 最终组合.positions.values() if p.total_amount > 0])
        
        print("4. 建仓结果:")
        print(f"   总资产: {最终组合.total_value:,.0f}元")
        print(f"   剩余现金: {最终组合.available_cash:,.0f}元")
        print(f"   持仓品种: {持仓品种数}只")
        
        # 验证结果
        assert 持仓品种数 >= 3
        assert 最终组合.market_value > 600000  # 大部分资金已投入
        
        print("✅ 策略工作流程完成")


if __name__ == "__main__":
    # 运行中文测试
    pytest.main([__file__, "-v", "-s"])