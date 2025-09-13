# EmuTrader 股票交易成本计算系统

## 概述

EmuTrader 实现了完整的A股交易成本计算系统，完全符合中国最新的股票交易规则。该系统支持佣金、印花税、过户费等各类交易费用的精确计算，并提供了灵活的配置接口。

## 交易成本组成

### 1. 佣金 (Commission)
- **买入**: 收取
- **卖出**: 收取
- **费率**: 万分之三 (0.0003)
- **最低限制**: 5元
- **计算公式**: `max(交易金额 × 0.0003, 5)`

### 2. 印花税 (Stamp Duty)
- **买入**: 不收取
- **卖出**: 收取
- **费率**: 千分之一 (0.001)
- **计算公式**: `交易金额 × 0.001`

### 3. 过户费 (Transfer Fee)
- **买入**: 收取
- **卖出**: 收取
- **费率**: 万分之零点一 (0.00001，即0.001%)
- **计算公式**: `交易金额 × 0.00001`

### 4. 总成本计算
```
总成本 = 佣金 + 印花税 + 过户费
实际支出 = 交易金额 + 总成本
```

## 核心实现

### OrderCost 类

```python
class OrderCost:
    def __init__(self, 
                 open_tax=0.0,                    # 买入印花税
                 close_tax=0.0,                   # 卖出印花税
                 open_commission=0.0,              # 买入佣金率
                 close_commission=0.0,             # 卖出佣金率
                 close_today_commission=0.0,       # 平今仓佣金
                 min_commission=0.0,               # 最低佣金
                 transfer_fee_rate=0.0):           # 过户费率
```

### calculate_cost 方法

```python
def calculate_cost(self, amount: int, price: float, direction: str = 'open', is_today: bool = False) -> tuple:
    """
    计算交易成本
    
    Args:
        amount: 交易数量
        price: 交易价格
        direction: 交易方向 ('open'=买入, 'close'=卖出)
        is_today: 是否平今仓
    
    Returns:
        tuple: (总成本, 佣金, 印花税, 过户费)
    """
```

## A股标准配置

### 默认配置

```python
# EmuTrader内置的A股标准配置
ashare_cost = OrderCost(
    open_tax=0,                    # 买入无印花税
    close_tax=0.001,               # 卖出千分之一印花税
    open_commission=0.0003,        # 买入万分之三佣金
    close_commission=0.0003,       # 卖出万分之三佣金
    close_today_commission=0,      # 无平今仓佣金（股票）
    min_commission=5,              # 最低佣金5元
    transfer_fee_rate=0.00001      # A股过户费率：0.001%
)
```

### 配置方式

```python
from emutrader import OrderCost, set_order_cost

# 设置股票交易成本
set_order_cost(ashare_cost, type='stock')

# 设置特定股票的交易成本
set_order_cost(specific_cost, type='stock', ref='000001.SZ')
```

## 计算示例

### 示例1：买入1000股，价格10.00元

```
交易金额 = 1000 × 10.00 = 10,000.00元
佣金 = max(10000 × 0.0003, 5) = 5.00元
印花税 = 0元（买入无印花税）
过户费 = 10000 × 0.00001 = 0.10元
总成本 = 5.00 + 0 + 0.10 = 5.10元
实际支出 = 10000.00 + 5.10 = 10,005.10元
```

### 示例2：卖出1500股，价格12.00元

```
交易金额 = 1500 × 12.00 = 18,000.00元
佣金 = max(18000 × 0.0003, 5) = 5.40元
印花税 = 18000 × 0.001 = 18.00元
过户费 = 18000 × 0.00001 = 0.18元
总成本 = 5.40 + 18.00 + 0.18 = 23.58元
实际获得 = 18000.00 - 23.58 = 17,976.42元
```

## 成本价计算

### 加权平均成本算法

```python
# 计算持仓成本价（包含交易成本）
def calculate_avg_cost(existing_amount, existing_cost, new_amount, new_price, commission, transfer_fee):
    """
    计算新的加权平均成本价
    
    Args:
        existing_amount: 现有持仓数量
        existing_cost: 现有成本价
        new_amount: 新买入数量
        new_price: 新买入价格
        commission: 佣金费用
        transfer_fee: 过户费用
    
    Returns:
        float: 新的加权平均成本价
    """
    # 计算新持仓的实际成本（包含交易成本）
    transaction_costs = commission + transfer_fee
    new_cost_with_fees = (new_price * new_amount + transaction_costs) / new_amount
    
    # 计算加权平均
    total_amount = existing_amount + new_amount
    if total_amount > 0:
        total_cost = existing_amount * existing_cost + new_amount * new_cost_with_fees
        return total_cost / total_amount
    return existing_cost
```

### 多次买入示例

假设三次买入交易：
1. 1000股 @ 10.00元，成本5.10元
2. 1500股 @ 12.00元，成本5.58元
3. 2000股 @ 9.50元，成本5.89元

```
第一次成本价 = (10000 + 5.10) / 1000 = 10.005100元/股
第二次成本价 = [(1000×10.005100) + (18000+5.58)] / 2500 = 11.204272元/股
第三次成本价 = [(2500×11.204272) + (19000+5.89)] / 4500 = 10.450000元/股
```

## API 使用

### 基本交易

```python
from emutrader import get_jq_account, set_order_cost, OrderCost, order_shares

# 创建账户
context = get_jq_account("my_strategy", 100000)

# 设置交易成本
ashare_cost = OrderCost(
    open_tax=0,
    close_tax=0.001,
    open_commission=0.0003,
    close_commission=0.0003,
    close_today_commission=0,
    min_commission=5,
    transfer_fee_rate=0.00001
)
set_order_cost(ashare_cost, type='stock')

# 执行交易（自动计算交易成本）
order_shares('000001.SZ', 1000, 10.00)  # 买入1000股，价格10.00元
```

### 自定义计算

```python
# 手动计算交易成本
ashare_cost = OrderCost(
    open_tax=0,
    close_tax=0.001,
    open_commission=0.0003,
    close_commission=0.0003,
    close_today_commission=0,
    min_commission=5,
    transfer_fee_rate=0.00001
)

# 计算买入成本
amount = 1000
price = 10.00
total_cost, commission, tax, transfer_fee = ashare_cost.calculate_cost(amount, price, 'open')

print(f"交易金额: {amount * price:.2f}元")
print(f"佣金: {commission:.2f}元")
print(f"印花税: {tax:.2f}元")
print(f"过户费: {transfer_fee:.4f}元")
print(f"总成本: {total_cost:.4f}元")
print(f"实际支出: {amount * price + total_cost:.2f}元")
```

## 精度和验证

### 计算精度
- **交易成本**: 精确到0.0001元
- **成本价**: 精确到0.01元（1分钱）
- **验证标准**: 实际支出与理论支出差异 < 0.01元

### 验证方法

```python
# 验证交易成本计算准确性
def verify_trading_cost():
    # 理论计算
    trade_value = amount * price
    theoretical_commission = max(trade_value * 0.0003, 5)
    theoretical_tax = trade_value * 0.001 if direction == 'close' else 0
    theoretical_transfer_fee = trade_value * 0.00001
    theoretical_total = theoretical_commission + theoretical_tax + theoretical_transfer_fee
    
    # 实际计算
    actual_total, actual_commission, actual_tax, actual_transfer_fee = ashare_cost.calculate_cost(amount, price, direction)
    
    # 验证精度
    assert abs(actual_total - theoretical_total) < 0.01
    assert abs(actual_commission - theoretical_commission) < 0.01
    assert abs(actual_tax - theoretical_tax) < 0.01
    assert abs(actual_transfer_fee - theoretical_transfer_fee) < 0.0001
```

## 注意事项

1. **最低佣金**: A股交易有5元最低佣金限制，小额交易需要注意
2. **过户费**: 买卖双向收取，费率为0.001%
3. **印花税**: 仅在卖出时收取，费率为0.1%
4. **成本价**: 包含佣金和过户费，不包含印花税（买入无印花税）
5. **精度要求**: 金融计算对精度要求高，建议使用decimal类型进行高精度计算

## 兼容性

- **API兼容**: 100%兼容JoinQuant API
- **向后兼容**: 现有代码无需修改
- **扩展性**: 支持自定义交易成本配置
- **多市场**: 支持股票、期货、基金等多种交易品种

## 相关文件

- `emutrader/core/models.py`: OrderCost类实现
- `emutrader/core/trader.py`: 交易执行逻辑
- `emutrader/core/context.py`: 账户上下文和交易成本处理
- `emutrader/api.py`: JoinQuant兼容API
- `examples/trading_cost_example.py`: 交易成本示例

---

*文档版本: v1.0*  
*最后更新: 2025年1月*  
*兼容版本: EmuTrader v0.1.4+*