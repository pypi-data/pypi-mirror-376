"""
中文测试用例示例
演示如何在测试中正确使用中文
"""

import pytest
from emutrader import get_jq_account, order_shares, order_target_percent


class TestChineseExample:
    """中文测试用例示例类"""
    
    @pytest.mark.example
    def test_chinese_strategy_name(self):
        """测试使用中文策略名称"""
        # 使用中文策略名称
        策略名称 = "我的量化策略"
        context = get_jq_account(策略名称, 100000, "STOCK")
        
        # 验证中文名称正确保存
        assert context.run_params['strategy_name'] == 策略名称
        
        print(f"[OK] 策略创建成功: {策略名称}")
    
    @pytest.mark.example  
    def test_chinese_stock_codes(self):
        """测试中文股票代码处理"""
        context = get_jq_account("股票测试", 100000)
        
        # 中文注释的股票列表
        股票池 = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A', 
            '600519.SH': '贵州茅台',
            '000858.SZ': '五粮液'
        }
        
        # 执行交易（使用中文变量名）
        for 股票代码, 股票名称 in 股票池.items():
            订单 = order_shares(股票代码, 100)
            print(f"[OK] 买入 {股票名称}({股票代码}): {订单.amount}股")
            
        # 验证持仓
        持仓数量 = len([p for p in context.portfolio.positions.values() 
                   if p.total_amount > 0])
        assert 持仓数量 >= 3
        
        print(f"[OK] 总持仓品种: {持仓数量}")
    
    def test_chinese_portfolio_analysis(self):
        """测试中文投资组合分析"""
        # 创建测试组合
        context = get_jq_account("组合分析测试", 200000)
        
        # 建仓
        股票配置 = [
            ("000001.SZ", "平安银行", 0.25),
            ("000002.SZ", "万科A", 0.20),
            ("600519.SH", "贵州茅台", 0.15),
        ]
        
        print("\n--- 建仓过程 ---")
        for 代码, 名称, 权重 in 股票配置:
            order_target_percent(代码, 权重)
            print(f"[OK] {名称}({代码}): 目标权重 {权重:.1%}")
            
        # 分析投资组合
        投资组合 = context.portfolio
        
        组合分析 = {
            "总资产": 投资组合.total_value,
            "可用资金": 投资组合.available_cash, 
            "持仓市值": 投资组合.market_value,
            "收益率": 投资组合.returns,
            "持仓数量": len([p for p in 投资组合.positions.values() 
                         if p.total_amount > 0])
        }
        
        print("\n--- 投资组合分析 ---")
        for 指标名, 指标值 in 组合分析.items():
            if 指标名 == "收益率":
                print(f"{指标名}: {指标值:.2%}")
            elif 指标名 == "持仓数量":
                print(f"{指标名}: {指标值}")
            else:
                print(f"{指标名}: {指标值:,.2f}")
                
        # 验证结果
        assert 组合分析["总资产"] > 150000
        assert 组合分析["持仓数量"] >= 3
        
        print("[PASS] 中文投资组合分析测试完成")
    
    def test_error_messages_in_chinese(self):
        """测试中文错误信息处理"""
        context = get_jq_account("错误测试", 1000)  # 只有1000元
        
        try:
            # 尝试买入超过资金的股票
            order_shares('000001.SZ', 10000, 100.0)  # 需要100万元
            assert False, "应该抛出异常"
            
        except Exception as e:
            错误信息 = str(e)
            print(f"[OK] 捕获到预期错误: {错误信息}")
            
        # 验证账户状态未变
        assert context.portfolio.available_cash == 1000
        print("[PASS] 错误处理测试通过")


class TestChineseSubPortfolio:
    """中文子账户测试"""
    
    def test_chinese_subportfolio_names(self):
        """测试中文子账户名称和管理"""
        from emutrader import set_subportfolios, SubPortfolioConfig, transfer_cash
        from emutrader.api import set_current_context
        
        # 创建策略
        context = get_jq_account("多账户策略", 500000)
        set_current_context(context)
        
        # 设置子账户（使用中文类型映射）
        账户配置 = [
            SubPortfolioConfig(cash=300000, type='stock'),      # 股票账户
            SubPortfolioConfig(cash=150000, type='futures'),    # 期货账户  
            SubPortfolioConfig(cash=50000, type='index_futures'), # 金融期货账户
        ]
        set_subportfolios(账户配置)
        
        # 中文账户类型映射
        账户类型映射 = {
            'STOCK': '股票账户',
            'FUTURE': '期货账户',
            'INDEX_FUTURE': '金融期货账户',
            'CREDIT': '信用账户'
        }
        
        print("\n--- 子账户状态 ---")
        for i, 子账户 in enumerate(context.subportfolios):
            账户名称 = 账户类型映射.get(子账户.type, 子账户.type)
            print(f"子账户{i}: {账户名称} - {子账户.available_cash:,.2f}元")
            
        # 测试资金转移
        转移金额 = 50000
        转移结果 = transfer_cash(from_pindex=1, to_pindex=0, cash=转移金额)
        
        assert 转移结果 is True
        print(f"[OK] 资金转移成功: {转移金额:,.2f}元从期货账户转入股票账户")
        
        # 验证转移后状态
        股票账户 = context.subportfolios[0]
        期货账户 = context.subportfolios[1]
        
        print(f"转移后股票账户余额: {股票账户.available_cash:,.2f}元")
        print(f"转移后期货账户余额: {期货账户.available_cash:,.2f}元")
        
        assert 股票账户.available_cash == 350000  # 300000 + 50000
        assert 期货账户.available_cash == 100000   # 150000 - 50000
        
        print("[PASS] 中文子账户管理测试完成")


class TestChineseIntegration:
    """中文集成测试"""
    
    def test_complete_chinese_strategy(self):
        """测试完整的中文策略流程"""
        # 模拟真实的中文策略
        def 策略初始化(context):
            """策略初始化函数"""
            # 设置股票池
            context.股票池 = {
                '000001.SZ': '平安银行',
                '000002.SZ': '万科A',
                '600519.SH': '贵州茅台', 
                '000858.SZ': '五粮液',
                '002415.SZ': '海康威视'
            }
            
            # 设置策略参数
            context.调仓频率 = 5
            context.最大单股权重 = 0.25
            context.计数器 = 0
            
            print(f"[OK] 策略初始化完成，股票池包含 {len(context.股票池)} 只股票")
            
        def 处理数据(context, data):
            """主要交易逻辑"""
            context.计数器 += 1
            
            print(f"\n=== 第{context.计数器}个交易周期 ===")
            
            # 获取当前组合状态
            组合 = context.portfolio
            print(f"当前总资产: {组合.total_value:,.2f}元")
            print(f"当前收益率: {组合.returns:.2%}")
            
            # 每N个周期调仓一次
            if context.计数器 % context.调仓频率 == 0:
                print("触发调仓逻辑")
                执行调仓(context)
            else:
                print("等待调仓周期")
                
        def 执行调仓(context):
            """调仓执行函数"""
            print("--- 开始调仓 ---")
            
            # 等权重分配
            目标权重 = 0.8 / len(context.股票池)  # 80%资金投入股票
            
            for 股票代码, 股票名称 in context.股票池.items():
                try:
                    订单 = order_target_percent(股票代码, 目标权重)
                    if 订单:
                        print(f"[OK] {股票名称}({股票代码}): 调整到{目标权重:.1%}")
                    else:
                        print(f"[FAIL] {股票名称}({股票代码}): 调仓失败")
                except Exception as e:
                    print(f"[ERROR] {股票名称}({股票代码}): 调仓异常 - {e}")
                    
            print("--- 调仓完成 ---")
            
        def 显示持仓(context):
            """显示当前持仓情况"""
            组合 = context.portfolio
            
            if len(组合.positions) == 0:
                print("当前无持仓")
                return
                
            print("--- 当前持仓明细 ---")
            for 证券代码, 持仓 in 组合.positions.items():
                if 持仓.total_amount > 0:
                    股票名称 = context.股票池.get(证券代码, "未知股票")
                    权重 = 持仓.value / 组合.total_value * 100
                    盈亏 = 持仓.pnl
                    
                    print(f"{股票名称}({证券代码}): "
                          f"{持仓.total_amount}股, "
                          f"权重:{权重:.1f}%, "
                          f"盈亏:{盈亏:+.2f}元")
        
        # 执行完整策略测试
        print("\n=== 完整中文策略测试 ===")
        
        # 创建策略上下文
        context = get_jq_account("中文策略测试", 500000, "STOCK")
        
        # 初始化策略
        策略初始化(context)
        
        # 模拟运行10个交易周期
        for 周期 in range(10):
            模拟数据 = {}  # 实际使用中会包含市场数据
            处理数据(context, 模拟数据)
            显示持仓(context)
            
        # 显示最终结果  
        print("\n=== 策略运行完成 ===")
        最终组合 = context.portfolio
        print(f"最终总资产: {最终组合.total_value:,.2f}元")
        print(f"总收益率: {最终组合.returns:.2%}")
        
        最终持仓数 = len([p for p in 最终组合.positions.values() 
                      if p.total_amount > 0])
        print(f"最终持仓品种: {最终持仓数}")
        
        # 验证策略执行结果
        assert 最终组合.total_value > 400000  # 考虑交易成本
        assert 最终持仓数 >= 4  # 至少持有4只股票
        
        print("[PASS] 完整中文策略测试通过")


if __name__ == "__main__":
    # 运行示例测试
    pytest.main([__file__, "-v", "-s"])