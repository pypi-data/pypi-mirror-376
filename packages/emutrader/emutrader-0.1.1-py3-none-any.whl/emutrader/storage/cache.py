# -*- coding: utf-8 -*-
"""
缓存管理器

实现LRU缓存机制，提供高性能的数据访问和存储。
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple, Set
from collections import OrderedDict
from datetime import datetime, timedelta

from ..exceptions import CacheException, CacheMissException, CacheExpiredException
from ..constants import Performance


class CacheManager:
    """
    缓存管理器
    
    提供LRU + TTL双重策略的高性能缓存系统，目标响应时间 < 10ms。
    
    Features:
    - LRU (Least Recently Used) 淘汰策略
    - TTL (Time To Live) 过期机制
    - 线程安全
    - 缓存命中率统计
    - 批量操作支持
    """
    
    def __init__(self, max_size=Performance.DEFAULT_CACHE_SIZE, 
                 ttl_seconds=Performance.DEFAULT_TTL,
                 storage_backend=None):
        """
        初始化缓存管理器
        
        Args:
            max_size (int): 最大缓存条目数
            ttl_seconds (int): 缓存过期时间（秒）
            storage_backend: 存储后端（用于缓存穿透时回源）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.storage_backend = storage_backend
        
        # 缓存数据结构
        self._cache = OrderedDict()  # 使用OrderedDict实现LRU
        self._expire_times = {}      # 过期时间映射
        self._lock = threading.RLock()  # 线程安全锁
        
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'expired': 0
        }
        
        # 性能监控
        self._last_cleanup = time.time()
        
    def get(self, key: str, default=None) -> Any:
        """
        获取缓存值
        
        Args:
            key (str): 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存的值或默认值
            
        Raises:
            CacheExpiredException: 缓存已过期
            CacheMissException: 缓存未命中且无默认值
        """
        with self._lock:
            start_time = time.time()
            
            try:
                # 检查缓存是否存在
                if key not in self._cache:
                    self._stats['misses'] += 1
                    if default is not None:
                        return default
                    raise CacheMissException(f"缓存未命中: {key}", cache_key=key)
                
                # 检查是否过期
                if self._is_expired(key):
                    self._remove_expired(key)
                    self._stats['expired'] += 1
                    if default is not None:
                        return default
                    raise CacheExpiredException(f"缓存已过期: {key}", cache_key=key)
                
                # 缓存命中，更新LRU顺序
                value = self._cache[key]
                self._cache.move_to_end(key)  # 移动到末尾（最近访问）
                self._stats['hits'] += 1
                
                return value
                
            finally:
                # 性能监控
                elapsed = (time.time() - start_time) * 1000  # 毫秒
                if elapsed > 10:  # 超过10ms记录警告
                    print(f"WARNING: Cache get operation took {elapsed:.2f}ms")
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key (str): 缓存键
            value (Any): 缓存值
            ttl_seconds (int, optional): 自定义TTL，不指定使用默认值
            
        Returns:
            bool: 是否成功设置
        """
        with self._lock:
            start_time = time.time()
            
            try:
                # 如果缓存已满，执行LRU淘汰
                while len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_lru()
                
                # 设置缓存值和过期时间
                self._cache[key] = value
                self._cache.move_to_end(key)  # 移动到末尾
                
                ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
                self._expire_times[key] = time.time() + ttl
                
                self._stats['sets'] += 1
                
                # 定期清理过期缓存
                if time.time() - self._last_cleanup > 60:  # 每分钟清理一次
                    self._cleanup_expired()
                
                return True
                
            finally:
                elapsed = (time.time() - start_time) * 1000
                if elapsed > 10:
                    print(f"WARNING: Cache set operation took {elapsed:.2f}ms")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._expire_times:
                    del self._expire_times[key]
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._expire_times.clear()
            # 重置统计信息（保留历史）
            cleared_items = len(self._cache)
            self._stats['deletes'] += cleared_items
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在且未过期
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否存在且有效
        """
        with self._lock:
            return key in self._cache and not self._is_expired(key)
    
    def get_or_set(self, key: str, factory_func, ttl_seconds: Optional[int] = None) -> Any:
        """
        获取缓存值，如果不存在则调用工厂函数生成并缓存
        
        Args:
            key (str): 缓存键
            factory_func: 生成值的函数
            ttl_seconds (int, optional): TTL
            
        Returns:
            Any: 缓存值或新生成的值
        """
        try:
            return self.get(key)
        except (CacheMissException, CacheExpiredException):
            # 缓存未命中或过期，生成新值
            value = factory_func()
            self.set(key, value, ttl_seconds)
            return value
    
    def batch_get(self, keys: list) -> Dict[str, Any]:
        """
        批量获取缓存值
        
        Args:
            keys (list): 缓存键列表
            
        Returns:
            Dict[str, Any]: 键值对字典（只包含存在且未过期的项）
        """
        result = {}
        with self._lock:
            for key in keys:
                try:
                    result[key] = self.get(key)
                except (CacheMissException, CacheExpiredException):
                    continue
        return result
    
    def batch_set(self, items: Dict[str, Any], ttl_seconds: Optional[int] = None) -> int:
        """
        批量设置缓存值
        
        Args:
            items (Dict[str, Any]): 键值对字典
            ttl_seconds (int, optional): TTL
            
        Returns:
            int: 成功设置的项目数
        """
        success_count = 0
        with self._lock:
            for key, value in items.items():
                if self.set(key, value, ttl_seconds):
                    success_count += 1
        return success_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'evictions': self._stats['evictions'],
                'expired': self._stats['expired'],
                'memory_usage_ratio': len(self._cache) / self.max_size
            }
    
    def _is_expired(self, key: str) -> bool:
        """检查键是否过期"""
        if key not in self._expire_times:
            return False
        return time.time() > self._expire_times[key]
    
    def _remove_expired(self, key: str) -> None:
        """移除过期的缓存项"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expire_times:
            del self._expire_times[key]
    
    def _evict_lru(self) -> None:
        """淘汰最近最少使用的缓存项"""
        if self._cache:
            # OrderedDict的第一个项是最久未访问的
            lru_key = next(iter(self._cache))
            del self._cache[lru_key]
            if lru_key in self._expire_times:
                del self._expire_times[lru_key]
            self._stats['evictions'] += 1
    
    def _cleanup_expired(self) -> None:
        """清理所有过期的缓存项"""
        current_time = time.time()
        expired_keys = []
        
        for key, expire_time in self._expire_times.items():
            if current_time > expire_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_expired(key)
            self._stats['expired'] += 1
        
        self._last_cleanup = current_time
    
    def __len__(self) -> int:
        """返回缓存项数量"""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """支持 'in' 操作符"""
        return self.exists(key)
    
    def __repr__(self) -> str:
        stats = self.get_cache_stats()
        return f"CacheManager(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']:.2%})"


class AccountCacheManager(CacheManager):
    """
    账户专用缓存管理器
    
    针对账户数据特点进行优化，支持账户状态、持仓、订单等数据的缓存。
    """
    
    def __init__(self, max_size=5000, ttl_seconds=300, storage_backend=None):
        """
        初始化账户缓存管理器
        
        Args:
            max_size (int): 最大缓存条目数（默认5000）
            ttl_seconds (int): 缓存过期时间（默认5分钟）
            storage_backend: 存储后端
        """
        super().__init__(max_size, ttl_seconds, storage_backend)
        
        # 账户数据专用分类缓存键前缀
        self.KEY_PREFIXES = {
            'account_state': 'acc_state:',
            'positions': 'pos:',
            'orders': 'ord:',
            'transactions': 'txn:',
            'performance': 'perf:'
        }
    
    def _make_account_key(self, prefix: str, strategy_name: str, account_id: int, 
                         suffix: str = '') -> str:
        """
        生成账户相关的缓存键
        
        Args:
            prefix (str): 键前缀
            strategy_name (str): 策略名称
            account_id (int): 账户ID
            suffix (str): 后缀
            
        Returns:
            str: 缓存键
        """
        key = f"{prefix}{strategy_name}:{account_id}"
        if suffix:
            key += f":{suffix}"
        return key
    
    def cache_account_state(self, strategy_name: str, account_id: int, account_state) -> bool:
        """缓存账户状态"""
        key = self._make_account_key(
            self.KEY_PREFIXES['account_state'], 
            strategy_name, 
            account_id
        )
        return self.set(key, account_state, ttl_seconds=60)  # 账户状态1分钟TTL
    
    def get_cached_account_state(self, strategy_name: str, account_id: int):
        """获取缓存的账户状态"""
        key = self._make_account_key(
            self.KEY_PREFIXES['account_state'], 
            strategy_name, 
            account_id
        )
        try:
            return self.get(key)
        except (CacheMissException, CacheExpiredException):
            return None
    
    def cache_positions(self, strategy_name: str, account_id: int, positions: dict) -> bool:
        """缓存持仓信息"""
        key = self._make_account_key(
            self.KEY_PREFIXES['positions'], 
            strategy_name, 
            account_id
        )
        return self.set(key, positions, ttl_seconds=120)  # 持仓2分钟TTL
    
    def get_cached_positions(self, strategy_name: str, account_id: int):
        """获取缓存的持仓信息"""
        key = self._make_account_key(
            self.KEY_PREFIXES['positions'], 
            strategy_name, 
            account_id
        )
        try:
            return self.get(key)
        except (CacheMissException, CacheExpiredException):
            return None
    
    def invalidate_account_cache(self, strategy_name: str, account_id: int) -> None:
        """清除账户相关的所有缓存"""
        patterns = [
            self._make_account_key(prefix, strategy_name, account_id)
            for prefix in self.KEY_PREFIXES.values()
        ]
        
        with self._lock:
            keys_to_delete = []
            for key in self._cache.keys():
                if any(key.startswith(pattern) for pattern in patterns):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.delete(key)
    
    def get_account_cache_stats(self, strategy_name: str, account_id: int) -> Dict[str, int]:
        """获取特定账户的缓存统计"""
        patterns = [
            self._make_account_key(prefix, strategy_name, account_id)
            for prefix in self.KEY_PREFIXES.values()
        ]
        
        stats = {prefix_name: 0 for prefix_name in self.KEY_PREFIXES.keys()}
        
        with self._lock:
            for key in self._cache.keys():
                for prefix_name, pattern in zip(self.KEY_PREFIXES.keys(), patterns):
                    if key.startswith(pattern):
                        stats[prefix_name] += 1
                        break
        
        return stats