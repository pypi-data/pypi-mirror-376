"""
中文测试用例最佳实践示例
正确的方式：英文函数名 + 中文文档字符串 + 中文变量名和注释
"""

import pytest
from emutrader import get_jq_account, order_shares, order_target_percent


class TestChineseDemo:
    """中文测试示例类 - 展示正确的中文测试方式"""
    
    @pytest.mark.demo
    def test_chinese_strategy_names(self):
        """测试中文策略名称支持"""
        # 创建使用中文名称的策略
        策略名称 = "我的量化策略"
        初始资金 = 100000
        
        context = get_jq_account(策略名称, 初始资金, "STOCK")
        
        # 验证中文策略名称保存正确
        assert context.run_params['strategy_name'] == 策略名称
        assert context.portfolio.total_value == 初始资金
        
        print(f"策略创建成功: {策略名称}, 初始资金: {初始资金:,}元")
    
    @pytest.mark.demo
    def test_chinese_stock_trading(self):
        """测试使用中文注释的股票交易"""
        # 创建测试策略
        context = get_jq_account("股票交易测试", 200000)
        
        # 定义股票池（使用中文注释）
        股票池 = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A', 
            '600519.SH': '贵州茅台'
        }
        
        # 执行买入操作
        交易结果 = []
        for 股票代码, 股票名称 in 股票池.items():
            订单 = order_shares(股票代码, 200)
            if 订单:
                交易结果.append((股票名称, 订单.amount))
                print(f"买入成功: {股票名称}({股票代码}) {订单.amount}股")
        
        # 验证交易结果
        assert len(交易结果) >= 2  # 至少成功交易2只股票
        
        # 检查账户状态
        投资组合 = context.portfolio
        持仓数量 = len([p for p in 投资组合.positions.values() if p.total_amount > 0])
        
        assert 持仓数量 >= 2
        assert 投资组合.market_value > 0
        
        print(f"交易完成，共持有 {持仓数量} 只股票")
    
    @pytest.mark.demo 
    def test_chinese_portfolio_analysis(self):
        """测试中文投资组合分析"""
        # 创建投资组合
        context = get_jq_account("组合分析", 300000)
        
        # 按比例建仓
        股票配置 = [
            ("000001.SZ", "平安银行", 0.20),
            ("000002.SZ", "万科A", 0.15),
            ("600519.SH", "贵州茅台", 0.10)
        ]
        
        print("建仓过程:")
        for 代码, 名称, 目标权重 in 股票配置:
            order_target_percent(代码, 目标权重)
            print(f"  {名称}({代码}): 目标权重 {目标权重:.1%}")
        
        # 分析投资组合
        组合 = context.portfolio
        
        分析结果 = {
            "总资产": 组合.total_value,
            "可用现金": 组合.available_cash,
            "持仓市值": 组合.market_value,
            "收益率": 组合.returns,
            "活跃持仓": len([p for p in 组合.positions.values() if p.total_amount > 0])
        }
        
        print("投资组合分析:")
        for 项目, 数值 in 分析结果.items():
            if 项目 == "收益率":
                print(f"  {项目}: {数值:.2%}")
            elif 项目 == "活跃持仓":
                print(f"  {项目}: {数值} 只")
            else:
                print(f"  {项目}: {数值:,.2f} 元")
        
        # 验证分析结果
        assert 分析结果["总资产"] >= 250000
        assert 分析结果["活跃持仓"] >= 3
        assert 分析结果["持仓市值"] > 0
        
        print("组合分析完成")


class TestChineseSubPortfolio:
    """中文子账户测试示例"""
    
    @pytest.mark.demo
    def test_chinese_multi_account_setup(self):
        """测试中文多账户设置"""
        from emutrader import set_subportfolios, SubPortfolioConfig, transfer_cash
        from emutrader.api import set_current_context
        
        # 创建主策略
        context = get_jq_account("多账户策略", 500000)
        set_current_context(context)
        
        # 配置子账户
        子账户配置 = [
            SubPortfolioConfig(cash=300000, type='stock'),      # 股票账户
            SubPortfolioConfig(cash=150000, type='futures'),    # 期货账户
            SubPortfolioConfig(cash=50000, type='index_futures') # 金融期货
        ]
        
        set_subportfolios(子账户配置)
        
        # 账户类型中文映射
        类型映射 = {
            'STOCK': '股票',
            'FUTURE': '期货', 
            'INDEX_FUTURE': '金融期货',
            'CREDIT': '信用'
        }
        
        print("子账户设置完成:")
        for i, 子账户 in enumerate(context.subportfolios):
            账户类型 = 类型映射.get(子账户.type, 子账户.type)
            资金 = 子账户.available_cash
            print(f"  账户{i}: {账户类型}账户 - {资金:,.0f}元")
        
        # 测试资金转移
        转移金额 = 30000
        转移成功 = transfer_cash(from_pindex=1, to_pindex=0, cash=转移金额)
        
        assert 转移成功 == True
        print(f"资金转移成功: {转移金额:,}元 从期货账户转入股票账户")
        
        # 验证转移结果
        股票账户 = context.subportfolios[0]
        期货账户 = context.subportfolios[1]
        
        assert 股票账户.available_cash == 330000  # 300000 + 30000
        assert 期货账户.available_cash == 120000   # 150000 - 30000
        
        print(f"转移后余额: 股票账户 {股票账户.available_cash:,}元, 期货账户 {期货账户.available_cash:,}元")


class TestChineseWorkflow:
    """中文完整工作流程测试"""
    
    @pytest.mark.demo
    def test_complete_chinese_workflow(self):
        """测试完整的中文策略工作流程"""
        
        print("=== 完整策略工作流程测试 ===")
        
        # 第1步: 创建策略
        策略名称 = "完整流程测试策略"
        初始资金 = 500000
        
        context = get_jq_account(策略名称, 初始资金)
        print(f"1. 策略创建: {策略名称}, 资金: {初始资金:,}元")
        
        # 第2步: 设置股票池
        股票池 = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A', 
            '600519.SH': '贵州茅台',
            '000858.SZ': '五粮液'
        }
        print(f"2. 股票池设置: {len(股票池)}只股票")
        
        # 第3步: 执行建仓
        print("3. 开始建仓:")
        等权重 = 0.8 / len(股票池)  # 80%资金等权重分配
        
        for 代码, 名称 in 股票池.items():
            订单 = order_target_percent(代码, 等权重)
            if 订单:
                print(f"   {名称}({代码}): 目标权重 {等权重:.1%}")
        
        # 第4步: 分析建仓结果
        组合 = context.portfolio
        
        建仓结果 = {
            "总资产": 组合.total_value,
            "剩余现金": 组合.available_cash,
            "股票市值": 组合.market_value,
            "资金使用率": 组合.market_value / 组合.total_value,
            "持仓数量": len([p for p in 组合.positions.values() if p.total_amount > 0])
        }
        
        print("4. 建仓结果分析:")
        for 指标, 数值 in 建仓结果.items():
            if 指标 == "资金使用率":
                print(f"   {指标}: {数值:.1%}")
            elif 指标 == "持仓数量":
                print(f"   {指标}: {数值}只")
            else:
                print(f"   {指标}: {数值:,.0f}元")
        
        # 第5步: 执行调仓（减少部分持仓）
        print("5. 执行调仓:")
        调仓操作 = [
            ("000001.SZ", "平安银行", 0.15),  # 从20%调到15%
            ("600519.SH", "贵州茅台", 0.25),  # 从20%调到25%
        ]
        
        for 代码, 名称, 新权重 in 调仓操作:
            order_target_percent(代码, 新权重)
            print(f"   {名称}({代码}): 调整到 {新权重:.1%}")
        
        # 第6步: 最终验证
        最终组合 = context.portfolio
        最终持仓 = len([p for p in 最终组合.positions.values() if p.total_amount > 0])
        
        print("6. 最终结果:")
        print(f"   总资产: {最终组合.total_value:,.0f}元")
        print(f"   收益率: {最终组合.returns:.2%}")
        print(f"   持仓品种: {最终持仓}只")
        
        # 验证流程执行结果
        assert 最终组合.total_value > 400000  # 考虑交易成本
        assert 最终持仓 >= 3  # 至少3只股票
        assert 最终组合.market_value > 300000  # 大部分资金已投入
        
        print("=== 完整流程测试通过 ===")


if __name__ == "__main__":
    # 运行中文测试示例
    print("运行中文测试用例示例...")
    pytest.main([__file__, "-v", "-s", "--tb=short"])