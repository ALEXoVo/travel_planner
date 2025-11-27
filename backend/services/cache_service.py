"""
缓存服务模块

提供基于本地文件的缓存功能，用于减少API调用成本。
支持自动过期、键值存储、类型化缓存管理。
"""
import os
import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# 缓存配置：各类型缓存的过期时间（秒）
CACHE_CONFIG = {
    'poi_search': 86400,      # POI搜索缓存24小时
    'poi_gates': 604800,      # 出入口数据缓存7天（变化少）
    'geocode': 2592000,       # 地理编码缓存30天（几乎不变）
    'distance': 86400,        # 距离计算缓存24小时
    'route': 3600,            # 路线规划缓存1小时（路况会变）
    'weather': 1800,          # 天气缓存30分钟
}


class CacheService:
    """
    缓存服务类

    使用本地文件系统存储缓存数据，按类型分目录管理。
    每个缓存项包含数据和过期时间戳。
    """

    def __init__(self, cache_dir: str = './cache'):
        """
        初始化缓存服务。

        Args:
            cache_dir: 缓存根目录路径
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dirs()
        logger.info(f"CacheService initialized with cache_dir: {self.cache_dir.absolute()}")

    def _ensure_cache_dirs(self) -> None:
        """确保所有缓存类型的目录存在"""
        for cache_type in CACHE_CONFIG.keys():
            cache_path = self.cache_dir / cache_type
            cache_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache directories ensured for types: {list(CACHE_CONFIG.keys())}")

    def _generate_key(self, **params) -> str:
        """
        生成缓存键（基于参数哈希）。

        将参数字典序列化为JSON字符串，再计算MD5哈希值作为缓存键。
        这确保相同参数生成相同的键，不同参数生成不同的键。

        Args:
            **params: 任意键值对参数

        Returns:
            str: 32位十六进制哈希字符串

        Examples:
            >>> service._generate_key(method='search', city='北京', keywords='景点')
            'a1b2c3d4e5f6...'
        """
        # 排序键以确保一致性
        key_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def _get_cache_file_path(self, cache_type: str, key: str) -> Path:
        """
        获取缓存文件路径。

        Args:
            cache_type: 缓存类型
            key: 缓存键

        Returns:
            Path: 缓存文件完整路径
        """
        return self.cache_dir / cache_type / f"{key}.json"

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        获取缓存数据，自动检查过期。

        Args:
            cache_type: 缓存类型（如 'poi_search', 'geocode'）
            key: 缓存键

        Returns:
            Optional[Any]: 缓存的数据，如果不存在或已过期则返回 None

        Examples:
            >>> data = service.get('poi_search', 'abc123')
            >>> if data:
            ...     print("Cache hit!")
        """
        if cache_type not in CACHE_CONFIG:
            logger.warning(f"Unknown cache type: {cache_type}")
            return None

        cache_file = self._get_cache_file_path(cache_type, key)

        if not cache_file.exists():
            logger.debug(f"Cache miss: {cache_type}/{key}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)

            # 检查过期
            current_time = time.time()
            if current_time > cache_entry['expires_at']:
                logger.debug(f"Cache expired: {cache_type}/{key}")
                # 删除过期文件
                cache_file.unlink()
                return None

            logger.info(f"Cache hit: {cache_type}/{key}")
            return cache_entry['data']

        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.error(f"Error reading cache {cache_type}/{key}: {str(e)}")
            # 删除损坏的缓存文件
            if cache_file.exists():
                cache_file.unlink()
            return None

    def set(self, cache_type: str, key: str, value: Any) -> None:
        """
        设置缓存，自动序列化为JSON并添加过期时间。

        Args:
            cache_type: 缓存类型
            key: 缓存键
            value: 要缓存的数据（必须可JSON序列化）

        Examples:
            >>> service.set('poi_search', 'abc123', {'name': '故宫', 'lat': 39.9})
        """
        if cache_type not in CACHE_CONFIG:
            logger.warning(f"Unknown cache type: {cache_type}, skipping cache")
            return

        cache_file = self._get_cache_file_path(cache_type, key)

        # 计算过期时间
        ttl = CACHE_CONFIG[cache_type]
        expires_at = time.time() + ttl

        cache_entry = {
            'data': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache set: {cache_type}/{key} (TTL: {ttl}s)")

        except (TypeError, IOError) as e:
            logger.error(f"Error writing cache {cache_type}/{key}: {str(e)}")

    def invalidate(self, cache_type: str, key: str = None) -> None:
        """
        清除缓存。

        如果指定 key，清除单个缓存项；
        如果不指定 key，清除该类型的所有缓存。

        Args:
            cache_type: 缓存类型
            key: 缓存键（可选）

        Examples:
            >>> service.invalidate('poi_search', 'abc123')  # 清除单个
            >>> service.invalidate('poi_search')             # 清除所有POI搜索缓存
        """
        if cache_type not in CACHE_CONFIG:
            logger.warning(f"Unknown cache type: {cache_type}")
            return

        if key:
            # 清除单个缓存项
            cache_file = self._get_cache_file_path(cache_type, key)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cache invalidated: {cache_type}/{key}")
        else:
            # 清除整个类型的所有缓存
            cache_dir = self.cache_dir / cache_type
            if cache_dir.exists():
                for cache_file in cache_dir.glob('*.json'):
                    cache_file.unlink()
                logger.info(f"All caches invalidated for type: {cache_type}")

    def get_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息。

        Returns:
            Dict[str, int]: 各类型缓存的文件数量

        Examples:
            >>> stats = service.get_stats()
            >>> print(stats)
            {'poi_search': 125, 'geocode': 342, ...}
        """
        stats = {}
        for cache_type in CACHE_CONFIG.keys():
            cache_dir = self.cache_dir / cache_type
            if cache_dir.exists():
                stats[cache_type] = len(list(cache_dir.glob('*.json')))
            else:
                stats[cache_type] = 0
        return stats

    def clear_expired(self) -> int:
        """
        清理所有已过期的缓存文件。

        Returns:
            int: 清理的文件数量

        Examples:
            >>> count = service.clear_expired()
            >>> print(f"Cleared {count} expired cache files")
        """
        cleared_count = 0
        current_time = time.time()

        for cache_type in CACHE_CONFIG.keys():
            cache_dir = self.cache_dir / cache_type
            if not cache_dir.exists():
                continue

            for cache_file in cache_dir.glob('*.json'):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)

                    if current_time > cache_entry.get('expires_at', 0):
                        cache_file.unlink()
                        cleared_count += 1

                except (json.JSONDecodeError, KeyError, IOError):
                    # 损坏的文件也删除
                    cache_file.unlink()
                    cleared_count += 1

        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} expired cache files")

        return cleared_count
