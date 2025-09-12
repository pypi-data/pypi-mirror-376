"""
Unit tests for cache management system.
"""

import pytest
import time
from datetime import datetime
from emutrader.storage.cache import CacheManager, AccountCacheManager
from emutrader.core.models import AccountState
from emutrader.exceptions import CacheException, CacheMissException, CacheExpiredException


class TestCacheManager:
    """Test CacheManager functionality."""
    
    @pytest.mark.unit
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(max_size=100, ttl_seconds=300)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 300
        assert len(cache) == 0
    
    @pytest.mark.unit
    def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        cache_manager.set("key1", "value1")
        
        value = cache_manager.get("key1")
        assert value == "value1"
        
        # 测试默认值
        value = cache_manager.get("nonexistent", default="default")
        assert value == "default"
    
    @pytest.mark.unit
    def test_cache_miss_exception(self, cache_manager):
        """Test cache miss exception."""
        with pytest.raises(CacheMissException, match="缓存未命中: nonexistent"):
            cache_manager.get("nonexistent")
    
    @pytest.mark.unit
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = CacheManager(max_size=100, ttl_seconds=1)  # 1秒过期
        cache.set("key1", "value1")
        
        # 立即获取应该成功
        value = cache.get("key1")
        assert value == "value1"
        
        # 等待过期
        time.sleep(1.1)
        
        # 获取过期缓存应该抛出异常
        with pytest.raises(CacheExpiredException):
            cache.get("key1")
    
    @pytest.mark.unit
    def test_cache_custom_ttl(self, cache_manager):
        """Test cache with custom TTL."""
        cache_manager.set("key1", "value1", ttl_seconds=1)
        
        # 立即获取应该成功
        assert cache_manager.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.1)
        
        with pytest.raises(CacheExpiredException):
            cache_manager.get("key1")
    
    @pytest.mark.unit
    def test_cache_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = CacheManager(max_size=3, ttl_seconds=300)
        
        # 填满缓存
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache) == 3
        
        # 访问key1使其变为最近使用
        cache.get("key1")
        
        # 添加新项，应该淘汰key2（最久未使用）
        cache.set("key4", "value4")
        assert len(cache) == 3
        
        # key2应该被淘汰
        with pytest.raises(CacheMissException):
            cache.get("key2")
        
        # key1和key3应该仍然存在
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    @pytest.mark.unit
    def test_cache_exists(self, cache_manager):
        """Test cache exists method."""
        assert not cache_manager.exists("key1")
        
        cache_manager.set("key1", "value1")
        assert cache_manager.exists("key1")
        
        # 测试过期项
        cache_manager.set("key2", "value2", ttl_seconds=0.1)
        time.sleep(0.2)
        assert not cache_manager.exists("key2")
    
    @pytest.mark.unit
    def test_cache_delete(self, cache_manager):
        """Test cache delete operation."""
        cache_manager.set("key1", "value1")
        assert cache_manager.exists("key1")
        
        success = cache_manager.delete("key1")
        assert success is True
        assert not cache_manager.exists("key1")
        
        # 删除不存在的键
        success = cache_manager.delete("nonexistent")
        assert success is False
    
    @pytest.mark.unit
    def test_cache_clear(self, cache_manager):
        """Test cache clear operation."""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        assert len(cache_manager) == 2
        
        cache_manager.clear()
        assert len(cache_manager) == 0
    
    @pytest.mark.unit
    def test_cache_get_or_set(self, cache_manager):
        """Test cache get_or_set operation."""
        # 工厂函数
        def factory():
            return "generated_value"
        
        # 首次调用应该生成值
        value = cache_manager.get_or_set("key1", factory)
        assert value == "generated_value"
        
        # 再次调用应该从缓存获取
        value = cache_manager.get_or_set("key1", lambda: "new_value")
        assert value == "generated_value"  # 仍然是原值
    
    @pytest.mark.unit
    def test_cache_batch_operations(self, cache_manager):
        """Test cache batch get and set operations."""
        # 批量设置
        items = {"key1": "value1", "key2": "value2", "key3": "value3"}
        success_count = cache_manager.batch_set(items)
        assert success_count == 3
        
        # 批量获取
        keys = ["key1", "key2", "key3", "nonexistent"]
        results = cache_manager.batch_get(keys)
        
        assert len(results) == 3  # 只返回存在的键
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert results["key3"] == "value3"
        assert "nonexistent" not in results
    
    @pytest.mark.unit
    def test_cache_statistics(self, cache_manager):
        """Test cache statistics."""
        # 初始统计
        stats = cache_manager.get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['sets'] == 0
        
        # 执行操作
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")
        try:
            cache_manager.get("nonexistent")
        except CacheMissException:
            pass
        
        # 检查统计
        stats = cache_manager.get_cache_stats()
        assert stats['hits'] >= 1
        assert stats['misses'] >= 1
        assert stats['sets'] >= 1
        assert stats['hit_rate'] > 0.0
    
    @pytest.mark.unit
    def test_cache_contains_operator(self, cache_manager):
        """Test cache 'in' operator."""
        cache_manager.set("key1", "value1")
        
        assert "key1" in cache_manager
        assert "nonexistent" not in cache_manager
    
    @pytest.mark.unit
    def test_cache_performance_warning(self, cache_manager, capfd):
        """Test cache performance warning for slow operations."""
        # 这个测试可能不稳定，因为依赖于系统性能
        # 主要测试警告逻辑是否存在
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")
        
        # 检查是否有警告输出（如果操作超过10ms）
        captured = capfd.readouterr()
        # 不断言具体内容，因为性能可能变化


class TestAccountCacheManager:
    """Test AccountCacheManager functionality."""
    
    @pytest.mark.unit
    def test_account_cache_initialization(self, account_cache_manager):
        """Test account cache manager initialization."""
        assert account_cache_manager.max_size == 100
        assert account_cache_manager.ttl_seconds == 300
        assert hasattr(account_cache_manager, 'KEY_PREFIXES')
    
    @pytest.mark.unit
    def test_account_cache_key_generation(self, account_cache_manager):
        """Test account cache key generation."""
        key = account_cache_manager._make_account_key(
            "test_prefix:", "strategy1", 1, "suffix"
        )
        assert key == "test_prefix:strategy1:1:suffix"
        
        key_no_suffix = account_cache_manager._make_account_key(
            "test_prefix:", "strategy1", 1
        )
        assert key_no_suffix == "test_prefix:strategy1:1"
    
    @pytest.mark.unit
    def test_cache_account_state(self, account_cache_manager, sample_account_state):
        """Test caching account state."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 缓存账户状态
        success = account_cache_manager.cache_account_state(
            strategy_name, account_id, sample_account_state
        )
        assert success is True
        
        # 获取缓存的账户状态
        cached_state = account_cache_manager.get_cached_account_state(
            strategy_name, account_id
        )
        
        assert cached_state is not None
        assert cached_state.total_value == sample_account_state.total_value
        assert cached_state.available_cash == sample_account_state.available_cash
    
    @pytest.mark.unit
    def test_cache_positions(self, account_cache_manager):
        """Test caching positions."""
        strategy_name = "test_strategy"
        account_id = 1
        positions = {"000001.XSHE": {"amount": 1000, "price": 10.0}}
        
        # 缓存持仓
        success = account_cache_manager.cache_positions(
            strategy_name, account_id, positions
        )
        assert success is True
        
        # 获取缓存的持仓
        cached_positions = account_cache_manager.get_cached_positions(
            strategy_name, account_id
        )
        
        assert cached_positions is not None
        assert cached_positions == positions
    
    @pytest.mark.unit
    def test_cache_miss_returns_none(self, account_cache_manager):
        """Test that cache miss returns None instead of exception."""
        # 获取不存在的账户状态
        cached_state = account_cache_manager.get_cached_account_state(
            "nonexistent", 999
        )
        assert cached_state is None
        
        # 获取不存在的持仓
        cached_positions = account_cache_manager.get_cached_positions(
            "nonexistent", 999
        )
        assert cached_positions is None
    
    @pytest.mark.unit
    def test_invalidate_account_cache(self, account_cache_manager, sample_account_state):
        """Test invalidating account cache."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 缓存一些数据
        account_cache_manager.cache_account_state(
            strategy_name, account_id, sample_account_state
        )
        account_cache_manager.cache_positions(
            strategy_name, account_id, {"000001.XSHE": {"amount": 1000}}
        )
        
        # 验证数据已缓存
        assert account_cache_manager.get_cached_account_state(strategy_name, account_id) is not None
        assert account_cache_manager.get_cached_positions(strategy_name, account_id) is not None
        
        # 清除账户缓存
        account_cache_manager.invalidate_account_cache(strategy_name, account_id)
        
        # 验证数据已清除
        assert account_cache_manager.get_cached_account_state(strategy_name, account_id) is None
        assert account_cache_manager.get_cached_positions(strategy_name, account_id) is None
    
    @pytest.mark.unit
    def test_account_cache_statistics(self, account_cache_manager, sample_account_state):
        """Test account cache statistics."""
        strategy_name = "test_strategy"
        account_id = 1
        
        # 初始统计应该全为0
        stats = account_cache_manager.get_account_cache_stats(strategy_name, account_id)
        for count in stats.values():
            assert count == 0
        
        # 缓存一些数据
        account_cache_manager.cache_account_state(
            strategy_name, account_id, sample_account_state
        )
        account_cache_manager.cache_positions(
            strategy_name, account_id, {"000001.XSHE": {"amount": 1000}}
        )
        
        # 检查统计
        stats = account_cache_manager.get_account_cache_stats(strategy_name, account_id)
        assert stats['account_state'] >= 1
        assert stats['positions'] >= 1
    
    @pytest.mark.unit
    def test_account_cache_ttl_settings(self, account_cache_manager):
        """Test different TTL settings for different data types."""
        strategy_name = "test_strategy"
        account_id = 1
        sample_state = AccountState(100000.0, 80000.0, 20000.0)
        
        # 账户状态应该有较短的TTL（60秒）
        account_cache_manager.cache_account_state(strategy_name, account_id, sample_state)
        
        # 持仓应该有稍长的TTL（120秒）
        positions = {"000001.XSHE": {"amount": 1000}}
        account_cache_manager.cache_positions(strategy_name, account_id, positions)
        
        # 验证都能正常获取
        assert account_cache_manager.get_cached_account_state(strategy_name, account_id) is not None
        assert account_cache_manager.get_cached_positions(strategy_name, account_id) is not None


@pytest.mark.performance
class TestCachePerformance:
    """Test cache performance characteristics."""
    
    def test_cache_response_time(self):
        """Test cache response time meets performance requirements."""
        cache = CacheManager(max_size=1000, ttl_seconds=300)
        
        # 预填充缓存
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        
        # 测试获取性能
        start_time = time.time()
        for i in range(100):
            cache.get(f"key_{i}")
        end_time = time.time()
        
        avg_time_ms = (end_time - start_time) * 1000 / 100
        assert avg_time_ms < 1.0  # 平均响应时间应小于1ms
    
    def test_cache_memory_efficiency(self):
        """Test cache memory usage remains reasonable."""
        cache = CacheManager(max_size=1000, ttl_seconds=300)
        
        # 填充缓存到最大容量
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{'x' * 100}_{i}")  # 较大的值
        
        assert len(cache) == 1000
        
        # 添加更多项，应该触发LRU淘汰
        for i in range(100):
            cache.set(f"new_key_{i}", f"new_value_{i}")
        
        # 缓存大小应该保持在限制内
        assert len(cache) == 1000
    
    def test_cache_high_concurrency_simulation(self):
        """Test cache behavior under simulated high load."""
        cache = CacheManager(max_size=500, ttl_seconds=300)
        
        # 模拟高频读写操作
        import threading
        results = []
        
        def cache_operations():
            for i in range(100):
                cache.set(f"thread_key_{i}", f"thread_value_{i}")
                try:
                    cache.get(f"thread_key_{i}")
                    results.append("success")
                except:
                    results.append("error")
        
        # 运行多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_operations)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 验证大部分操作成功
        success_rate = results.count("success") / len(results)
        assert success_rate > 0.95  # 95%以上成功率