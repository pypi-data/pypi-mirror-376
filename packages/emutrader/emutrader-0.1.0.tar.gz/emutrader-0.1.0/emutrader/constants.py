# -*- coding: utf-8 -*-
"""
QSM Account 常量定义

统一管理系统中使用的所有常量，便于维护和修改。
"""

# 账户类型常量
class AccountTypes:
    """账户类型常量"""
    STOCK = "STOCK"           # 股票账户
    FUTURE = "FUTURE"         # 期货账户  
    CREDIT = "CREDIT"         # 融资融券账户
    OPTION = "OPTION"         # 期权账户
    CRYPTO = "CRYPTO"         # 数字货币账户
    
    # 所有支持的账户类型
    ALL = [STOCK, FUTURE, CREDIT, OPTION, CRYPTO]
    
    # 已实现的账户类型
    IMPLEMENTED = [STOCK, FUTURE, CREDIT]
    
    # 开发中的账户类型
    IN_DEVELOPMENT = [OPTION, CRYPTO]

# 订单状态常量 (兼容JoinQuant)
class OrderStatus:
    """订单状态常量"""
    NEW = "new"                    # 新建
    OPEN = "open"                  # 未成交
    FILLED = "filled"              # 已成交
    CANCELLED = "cancelled"        # 已撤销
    REJECTED = "rejected"          # 已拒绝
    HELD = "held"                  # 暂停
    
    # 所有状态
    ALL = [NEW, OPEN, FILLED, CANCELLED, REJECTED, HELD]
    
    # 终结状态
    FINAL_STATES = [FILLED, CANCELLED, REJECTED]
    
    # 活跃状态
    ACTIVE_STATES = [NEW, OPEN, HELD]

# 订单类型常量
class OrderType:
    """订单类型常量"""
    MARKET = "market"              # 市价单
    LIMIT = "limit"                # 限价单
    STOP = "stop"                  # 停损单
    STOP_LIMIT = "stop_limit"      # 停损限价单
    
    # 所有类型
    ALL = [MARKET, LIMIT, STOP, STOP_LIMIT]

# 交易方向常量
class Direction:
    """交易方向常量"""
    BUY = "buy"                    # 买入
    SELL = "sell"                  # 卖出
    SHORT = "short"                # 做空
    COVER = "cover"                # 平仓
    
    # 所有方向
    ALL = [BUY, SELL, SHORT, COVER]
    
    # 开仓方向
    OPEN_DIRECTIONS = [BUY, SHORT]
    
    # 平仓方向  
    CLOSE_DIRECTIONS = [SELL, COVER]

# 存储类型常量
class StorageTypes:
    """存储类型常量"""
    SQLITE = "sqlite"              # SQLite数据库
    MEMORY = "memory"              # 内存存储
    MYSQL = "mysql"                # MySQL数据库 (未实现)
    POSTGRESQL = "postgresql"      # PostgreSQL数据库 (未实现)
    
    # 已实现的存储类型
    IMPLEMENTED = [SQLITE, MEMORY]

# 缓存策略常量
class CacheStrategy:
    """缓存策略常量"""
    LRU = "lru"                    # 最近最少使用
    LFU = "lfu"                    # 最少使用频率
    FIFO = "fifo"                  # 先进先出
    TTL = "ttl"                    # 时间过期
    
    # 默认策略
    DEFAULT = LRU

# 适配器类型常量
class AdapterTypes:
    """适配器类型常量"""
    JQ = "joinquant"               # JoinQuant适配器
    JQ_LEGACY = "jq_legacy"        # JQ兼容适配器
    QMT = "qmt"                    # QMT适配器
    MOCK = "mock"                  # 模拟适配器
    FUTURES = "futures"            # 期货适配器
    
    # 所有类型
    ALL = [JQ, JQ_LEGACY, QMT, MOCK, FUTURES]

# 风险管理常量
class RiskLimits:
    """风险管理限制常量"""
    MAX_POSITION_RATIO = 0.95      # 最大仓位比例
    MAX_SINGLE_STOCK_RATIO = 0.10  # 单只股票最大比例
    MIN_CASH_RATIO = 0.05          # 最小现金比例
    MAX_LEVERAGE = 3.0             # 最大杠杆倍数
    
    # 期货专用
    FUTURES_MARGIN_RATIO = 0.15    # 期货保证金比例
    MAX_FUTURES_LEVERAGE = 10.0    # 期货最大杠杆

# 性能相关常量
class Performance:
    """性能相关常量"""
    DEFAULT_CACHE_SIZE = 1000      # 默认缓存大小
    DEFAULT_TTL = 300              # 默认TTL(秒)
    MAX_BATCH_SIZE = 1000          # 批量操作最大大小
    CONNECTION_POOL_SIZE = 5       # 连接池大小
    QUERY_TIMEOUT = 30             # 查询超时时间(秒)

# 数据库相关常量
class Database:
    """数据库相关常量"""
    DEFAULT_DB_NAME = "emutrader_account_{account_id}.db"
    SCHEMA_VERSION = "1.0.0"
    
    # 表名
    ACCOUNT_TABLE = "account"
    POSITION_TABLE = "position" 
    ORDER_TABLE = "order"
    TRANSACTION_TABLE = "transaction"
    CASH_TRANSFER_TABLE = "cash_transfer"


# 期货合约基本信息
class FuturesProducts:
    """期货品种合约信息"""
    PRODUCTS = {
        # 郑商所 (CZCE)
        "AP": {"name": "苹果", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FD0900"},
        "CF": {"name": "郑棉", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN2300"},
        "SA": {"name": "纯碱", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FN2300"},
        "SH": {"name": "烧碱", "exchange": "CZCE", "volume_multiple": 30, "price_tick": 1.0, "session": "FN2300"},
        "JR": {"name": "粳稻", "exchange": "CZCE", "volume_multiple": 30, "price_tick": 1.0, "session": "FD0900"},
        "TA": {"name": "PTA", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 2.0, "session": "FN2300"},
        "MA": {"name": "郑醇", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "SR": {"name": "白糖", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "ZC": {"name": "郑煤", "exchange": "CZCE", "volume_multiple": 100, "price_tick": 0.2, "session": "FN2300"},
        "RM": {"name": "菜粕", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "PF": {"name": "短纤", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 2.0, "session": "FN2300"},
        "CJ": {"name": "红枣", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 5.0, "session": "FD0900"},
        "UR": {"name": "尿素", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FN2300"},
        "PK": {"name": "花生", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 2.0, "session": "FD0900"},
        "OI": {"name": "菜油", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "FG": {"name": "玻璃", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FN2300"},
        "SF": {"name": "硅铁", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 2.0, "session": "FN2300"},
        "SM": {"name": "锰硅", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 2.0, "session": "FN2300"},
        "CY": {"name": "棉纱", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN2300"},
        "PX": {"name": "对二甲苯", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "WH": {"name": "郑麦", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FD0900"},
        "RI": {"name": "早籼稻", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FD0900"},
        "LR": {"name": "晚籼稻", "exchange": "CZCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FD0900"},
        "PM": {"name": "普麦", "exchange": "CZCE", "volume_multiple": 50, "price_tick": 1.0, "session": "FD0900"},
        "RS": {"name": "菜籽", "exchange": "CZCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FD0900"},
        "PL": {"name": "丙烯", "exchange": "CZCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FD0900"},

        # 上期所 (SHFE)
        "cu": {"name": "沪铜", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 10.0, "session": "FN0100"},
        "al": {"name": "沪铝", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN0100"},
        "zn": {"name": "沪锌", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN0100"},
        "ni": {"name": "沪镍", "exchange": "SHFE", "volume_multiple": 1, "price_tick": 10.0, "session": "FN0100"},
        "au": {"name": "沪金", "exchange": "SHFE", "volume_multiple": 1000, "price_tick": 0.02, "session": "FN0230"},
        "ag": {"name": "沪银", "exchange": "SHFE", "volume_multiple": 15, "price_tick": 1.0, "session": "FN0230"},
        "rb": {"name": "螺纹钢", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "hc": {"name": "热卷", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "ru": {"name": "橡胶", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 5.0, "session": "FN2300"},
        "bu": {"name": "沥青", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 2.0, "session": "FN2300"},
        "fu": {"name": "燃油", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "sp": {"name": "纸浆", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 2.0, "session": "FN2300"},
        "nr": {"name": "20胶", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 5.0, "session": "FN2300"},
        "ss": {"name": "不锈钢", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN0100"},
        "pb": {"name": "沪铅", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN0100"},
        "sn": {"name": "沪锡", "exchange": "SHFE", "volume_multiple": 1, "price_tick": 10.0, "session": "FN0100"},
        "wr": {"name": "线材", "exchange": "SHFE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "ad": {"name": "铝合金", "exchange": "SHFE", "volume_multiple": 5, "price_tick": 2.0, "session": "FD0900"},

        # 能源中心 (INE)
        "sc": {"name": "原油", "exchange": "INE", "volume_multiple": 1000, "price_tick": 0.1, "session": "FN0230"},
        "lu": {"name": "低硫油", "exchange": "INE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "bc": {"name": "国际铜", "exchange": "INE", "volume_multiple": 5, "price_tick": 10.0, "session": "FN0100"},

        # 大商所 (DCE)
        "a": {"name": "豆一", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "m": {"name": "豆粕", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "y": {"name": "豆油", "exchange": "DCE", "volume_multiple": 10, "price_tick": 2.0, "session": "FN2300"},
        "p": {"name": "棕榈油", "exchange": "DCE", "volume_multiple": 10, "price_tick": 2.0, "session": "FN2300"},
        "c": {"name": "玉米", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "i": {"name": "铁矿石", "exchange": "DCE", "volume_multiple": 100, "price_tick": 0.5, "session": "FN2300"},
        "j": {"name": "焦炭", "exchange": "DCE", "volume_multiple": 100, "price_tick": 0.5, "session": "FN2300"},
        "jm": {"name": "焦煤", "exchange": "DCE", "volume_multiple": 60, "price_tick": 0.5, "session": "FN2300"},
        "l": {"name": "塑料", "exchange": "DCE", "volume_multiple": 5, "price_tick": 5.0, "session": "FN2300"},
        "v": {"name": "PVC", "exchange": "DCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "pp": {"name": "聚丙烯", "exchange": "DCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "eg": {"name": "乙二醇", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "eb": {"name": "苯乙烯", "exchange": "DCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "lh": {"name": "生猪", "exchange": "DCE", "volume_multiple": 16, "price_tick": 5.0, "session": "FD0900"},
        "rr": {"name": "粳米", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FD0900"},
        "lc": {"name": "碳酸锂", "exchange": "DCE", "volume_multiple": 1, "price_tick": 1.0, "session": "FN2300"},
        "si": {"name": "工业硅", "exchange": "DCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "ec": {"name": "集运欧线", "exchange": "DCE", "volume_multiple": 1, "price_tick": 1.0, "session": "FN2300"},
        "pg": {"name": "液化气", "exchange": "DCE", "volume_multiple": 20, "price_tick": 1.0, "session": "FN2300"},
        "ao": {"name": "氧化铝", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "b": {"name": "豆二", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "fb": {"name": "纤板", "exchange": "DCE", "volume_multiple": 500, "price_tick": 0.05, "session": "FD0900"},
        "bb": {"name": "胶板", "exchange": "DCE", "volume_multiple": 400, "price_tick": 0.05, "session": "FD0900"},
        "jd": {"name": "鸡蛋", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FD0900"},
        "cs": {"name": "淀粉", "exchange": "DCE", "volume_multiple": 10, "price_tick": 1.0, "session": "FN2300"},
        "bz": {"name": "纯苯", "exchange": "DCE", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},

        # 中金所 (CFFEX)  
        "IF": {"name": "沪深300", "exchange": "CFFEX", "volume_multiple": 300, "price_tick": 0.2, "session": "SD0930"},
        "IC": {"name": "中证500", "exchange": "CFFEX", "volume_multiple": 200, "price_tick": 0.2, "session": "SD0930"},
        "IH": {"name": "上证50", "exchange": "CFFEX", "volume_multiple": 300, "price_tick": 0.2, "session": "SD0930"},
        "IM": {"name": "1000股指", "exchange": "CFFEX", "volume_multiple": 200, "price_tick": 0.2, "session": "SD0930"},
        "T": {"name": "10年国债", "exchange": "CFFEX", "volume_multiple": 10000, "price_tick": 0.005, "session": "SD0930"},
        "TF": {"name": "5年国债", "exchange": "CFFEX", "volume_multiple": 10000, "price_tick": 0.005, "session": "SD0930"},
        "TS": {"name": "2年债", "exchange": "CFFEX", "volume_multiple": 20000, "price_tick": 0.005, "session": "SD0930"},
        "TL": {"name": "三十年债", "exchange": "CFFEX", "volume_multiple": 10000, "price_tick": 0.005, "session": "SD0930"},

        # 广期所 (GFEX)
        "br": {"name": "BR橡胶", "exchange": "GFEX", "volume_multiple": 10, "price_tick": 5.0, "session": "FN2300"},
        "PR": {"name": "瓶片", "exchange": "GFEX", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
        "lg": {"name": "原木", "exchange": "GFEX", "volume_multiple": 10, "price_tick": 0.5, "session": "FD0900"},
        "ps": {"name": "多晶硅", "exchange": "GFEX", "volume_multiple": 5, "price_tick": 1.0, "session": "FN2300"},
    }
    
    @classmethod
    def get_product_info(cls, symbol: str) -> dict:
        """获取期货品种信息"""
        return cls.PRODUCTS.get(symbol.upper())
    
    @classmethod 
    def get_volume_multiple(cls, symbol: str) -> int:
        """获取合约乘数"""
        info = cls.get_product_info(symbol)
        return info["volume_multiple"] if info else 1
    
    @classmethod
    def get_price_tick(cls, symbol: str) -> float:
        """获取最小变动价位"""
        info = cls.get_product_info(symbol)
        return info["price_tick"] if info else 1.0
    
    @classmethod
    def get_exchange(cls, symbol: str) -> str:
        """获取交易所"""
        info = cls.get_product_info(symbol)
        return info["exchange"] if info else "UNKNOWN"

# JoinQuant兼容性常量
class JQCompatibility:
    """JoinQuant兼容性常量"""
    API_VERSION = "2.0+"
    DEFAULT_BENCHMARK = "000300.XSHG"  # 沪深300
    DEFAULT_FREQ = "daily"
    DEFAULT_REFRESH_RATE = 1           # 刷新频率(秒)

# 错误代码常量
class ErrorCodes:
    """错误代码常量"""
    # 通用错误
    UNKNOWN_ERROR = 1000
    INVALID_PARAMETER = 1001
    PERMISSION_DENIED = 1002
    
    # 存储错误
    STORAGE_ERROR = 2000
    DATABASE_ERROR = 2001
    CONNECTION_ERROR = 2002
    
    # 适配器错误
    ADAPTER_ERROR = 3000
    PLATFORM_ERROR = 3001
    API_ERROR = 3002
    
    # 验证错误
    VALIDATION_ERROR = 4000
    DATA_INTEGRITY_ERROR = 4001
    
    # 缓存错误
    CACHE_ERROR = 5000
    CACHE_MISS = 5001
    CACHE_EXPIRED = 5002

# 日志级别常量
class LogLevel:
    """日志级别常量"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# 默认配置常量
class Defaults:
    """默认配置常量"""
    INITIAL_CASH = 100000          # 默认初始资金
    ACCOUNT_TYPE = AccountTypes.STOCK
    STORAGE_TYPE = StorageTypes.SQLITE
    CACHE_STRATEGY = CacheStrategy.LRU
    ADAPTER_TYPE = AdapterTypes.JQ_LEGACY
    
    # 路径配置
    DATA_DIR = "data"
    LOG_DIR = "logs" 
    CONFIG_DIR = "configs"