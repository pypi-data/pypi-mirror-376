#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EmuTrader 交易成本设置示例

演示如何使用set_order_cost函数设置不同交易品种的交易成本
"""

from emutrader import get_jq_account, OrderCost, set_order_cost, order_shares, order_value

def main():
    print("=== EmuTrader 交易成本设置示例 ===\n")
    
    # 1. 创建策略上下文
    context = get_jq_account("trading_cost_example", 100000)
    print(f"初始资金: {context.portfolio.available_cash:.2f}")
    
    # 2. 设置股票交易成本（标准A股配置）
    print("\n1. 设置股票交易成本...")
    stock_cost = OrderCost(
        open_tax=0,                    # 买入无印花税
        close_tax=0.001,              # 卖出千分之一印花税
        open_commission=0.0003,       # 买入万分之三佣金
        close_commission=0.0003,      # 卖出万分之三佣金
        close_today_commission=0,      # 无平今仓佣金（股票）
        min_commission=5               # 最低佣金5元
    )
    set_order_cost(stock_cost, type='stock')
    print("✓ 股票交易成本设置完成")
    
    # 3. 设置期货交易成本
    print("\n2. 设置期货交易成本...")
    futures_cost = OrderCost(
        open_tax=0,                   # 期货无印花税
        close_tax=0,                  # 期货无印花税
        open_commission=0.000023,     # 开仓万分之0.23
        close_commission=0.000023,    # 平仓万分之0.23
        close_today_commission=0.0023, # 平今仓万分之23
        min_commission=0               # 无最低佣金
    )
    set_order_cost(futures_cost, type='futures')
    print("✓ 期货交易成本设置完成")
    
    # 4. 设置特定股票的交易成本
    print("\n3. 设置特定股票交易成本...")
    specific_stock_cost = OrderCost(
        open_tax=0,
        close_tax=0.001,
        open_commission=0.0002,       # 更低的佣金率
        close_commission=0.0002,
        close_today_commission=0,
        min_commission=1               # 更低的最低佣金
    )
    set_order_cost(specific_stock_cost, type='stock', ref='000001.SZ')
    print("✓ 特定股票(000001.SZ)交易成本设置完成")
    
    # 5. 演示交易成本计算
    print("\n4. 交易成本计算演示...")
    
    # 模拟计算买入1000股，价格10元的成本
    amount = 1000
    price = 10.0
    trade_value = amount * price
    
    # 使用股票标准成本计算
    total_cost, commission, tax, transfer_fee = stock_cost.calculate_cost(amount, price, 'open')
    
    print(f"交易信息:")
    print(f"  - 证券: 000001.SZ")
    print(f"  - 数量: {amount}股")
    print(f"  - 价格: {price:.2f}元")
    print(f"  - 交易金额: {trade_value:.2f}元")
    print(f"交易成本:")
    print(f"  - 佣金: {commission:.2f}元")
    print(f"  - 印花税: {tax:.2f}元")
    print(f"  - 过户费: {transfer_fee:.4f}元")
    print(f"  - 总成本: {total_cost:.2f}元")
    print(f"  - 实际需要资金: {trade_value + total_cost:.2f}元")
    
    # 6. 执行实际交易
    print(f"\n5. 执行实际交易...")
    initial_cash = context.portfolio.available_cash
    print(f"交易前可用资金: {initial_cash:.2f}元")
    
    # 执行买入订单
    order_result = order_shares('000001.SZ', amount)
    
    if order_result:
        final_cash = context.portfolio.available_cash
        cash_used = initial_cash - final_cash
        print(f"交易后可用资金: {final_cash:.2f}元")
        print(f"实际使用资金: {cash_used:.2f}元")
        print(f"成本差异: {abs(cash_used - (trade_value + total_cost)):.2f}元")
        
        # 查看持仓信息
        position = context.portfolio.get_position('000001.SZ')
        if position and position.total_amount > 0:
            print(f"\n持仓信息:")
            print(f"  - 持仓数量: {position.total_amount}股")
            print(f"  - 平均成本: {position.avg_cost:.4f}元")
            print(f"  - 持仓市值: {position.value:.2f}元")
            print(f"  - 持仓盈亏: {position.pnl:.2f}元")
    else:
        print("❌ 交易执行失败")
    
    print("\n=== 交易成本设置示例完成 ===")


if __name__ == "__main__":
    main()