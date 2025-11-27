"""
高德地图API服务模块

封装所有与高德地图API交互的功能，包括POI搜索、地理编码、
路径规划、天气查询等。
"""
import requests
from typing import Dict, List, Tuple, Optional, Any
import logging
from config import Config
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class AmapService:
    """高德地图API服务类"""

    def __init__(self, api_key: str = None, timeout: int = None, enable_cache: bool = True):
        """
        初始化高德地图服务。

        Args:
            api_key: 高德地图API密钥，默认从配置读取
            timeout: 请求超时时间（秒），默认从配置读取
            enable_cache: 是否启用缓存，默认True
        """
        self.api_key = api_key or Config.AMAP_API_KEY
        self.timeout = timeout or Config.AMAP_TIMEOUT
        self.cache = CacheService() if enable_cache else None

        if not self.api_key:
            logger.warning("AMap API key not configured")

        if self.cache:
            logger.info("AmapService initialized with caching enabled")

    def search_pois(
        self,
        city: str,
        keywords: str = '',
        poi_type: str = '',
        offset: int = 100,
        page: int = 1,
        extensions: str = 'all'
    ) -> List[Dict[str, Any]]:
        """
        搜索POI（兴趣点）。

        Args:
            city: 城市名称
            keywords: 关键词
            poi_type: POI类型
            offset: 返回数量
            page: 页码
            extensions: 返回结果详细程度（base/all）

        Returns:
            List[Dict]: POI列表

        Raises:
            requests.RequestException: 请求失败时抛出
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='search_pois',
                city=city,
                keywords=keywords,
                poi_type=poi_type,
                offset=offset,
                page=page,
                extensions=extensions
            )
            cached_result = self.cache.get('poi_search', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            params = {
                'key': self.api_key,
                'keywords': keywords,
                'types': poi_type,
                'city': city,
                'citylimit': 'true',
                'offset': offset,
                'page': page,
                'extensions': extensions
            }

            response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = data.get('pois', [])

            # 写入缓存
            if self.cache:
                self.cache.set('poi_search', cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error searching POIs: {str(e)}")
            return []

    def search_scenic_spots(self, city: str) -> List[Dict]:
        """搜索风景名胜"""
        config = Config.POI_SEARCH_CONFIG['scenic']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def search_food(self, city: str) -> List[Dict]:
        """搜索餐饮服务"""
        config = Config.POI_SEARCH_CONFIG['food']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def search_hotels(self, city: str) -> List[Dict]:
        """搜索住宿服务"""
        config = Config.POI_SEARCH_CONFIG['hotel']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def search_cultural(self, city: str) -> List[Dict]:
        """搜索文化场所"""
        config = Config.POI_SEARCH_CONFIG['cultural']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def search_shopping(self, city: str) -> List[Dict]:
        """搜索购物场所"""
        config = Config.POI_SEARCH_CONFIG['shopping']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def search_parent_child(self, city: str) -> List[Dict]:
        """搜索亲子场所"""
        config = Config.POI_SEARCH_CONFIG['parent_child']
        return self.search_pois(
            city=city,
            keywords=config['keywords'],
            poi_type=config['types'],
            offset=config['offset']
        )

    def geocode(self, address: str, city: str = None) -> Optional[Tuple[float, float]]:
        """
        地理编码：地址转坐标。

        Args:
            address: 地址字符串
            city: 城市名称（可选，用于提高准确度）

        Returns:
            Optional[Tuple[float, float]]: (经度, 纬度)，失败返回None
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='geocode',
                address=address,
                city=city or ''
            )
            cached_result = self.cache.get('geocode', cache_key)
            if cached_result is not None:
                # 缓存的是列表，需要转回元组
                return tuple(cached_result) if isinstance(cached_result, list) else cached_result

        try:
            params = {
                'key': self.api_key,
                'address': address
            }
            if city:
                params['city'] = city

            response = requests.get(
                "https://restapi.amap.com/v3/geocode/geo",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('geocodes'):
                location_str = data['geocodes'][0]['location']
                lng, lat = map(float, location_str.split(','))
                result = (lng, lat)

                # 写入缓存（元组转列表以便JSON序列化）
                if self.cache:
                    self.cache.set('geocode', cache_key, list(result))

                return result

            return None

        except Exception as e:
            logger.error(f"Geocode error for {address}: {str(e)}")
            return None

    def reverse_geocode(self, lng: float, lat: float) -> Optional[Dict[str, Any]]:
        """
        逆地理编码：坐标转地址。

        Args:
            lng: 经度
            lat: 纬度

        Returns:
            Optional[Dict]: 地址信息，失败返回None
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='reverse_geocode',
                lng=lng,
                lat=lat
            )
            cached_result = self.cache.get('geocode', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            params = {
                'key': self.api_key,
                'location': f"{lng},{lat}"
            }

            response = requests.get(
                "https://restapi.amap.com/v3/geocode/regeo",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1':
                result = data.get('regeocode', {})

                # 写入缓存
                if self.cache:
                    self.cache.set('geocode', cache_key, result)

                return result

            return None

        except Exception as e:
            logger.error(f"Reverse geocode error for ({lng}, {lat}): {str(e)}")
            return None

    def get_distance(
        self,
        origins: str,
        destination: str,
        dist_type: str = '1'
    ) -> Tuple[int, int]:
        """
        获取距离和时间（直线距离或驾车距离）。

        Args:
            origins: 起点坐标 "lng,lat"
            destination: 终点坐标 "lng,lat"
            dist_type: 距离类型（1:直线距离, 0:驾车导航距离）

        Returns:
            Tuple[int, int]: (距离(米), 时间(秒))
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_distance',
                origins=origins,
                destination=destination,
                dist_type=dist_type
            )
            cached_result = self.cache.get('distance', cache_key)
            if cached_result is not None:
                return tuple(cached_result) if isinstance(cached_result, list) else cached_result

        try:
            params = {
                'key': self.api_key,
                'origins': origins,
                'destination': destination,
                'type': dist_type
            }

            response = requests.get(
                "https://restapi.amap.com/v3/distance",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('results'):
                result_data = data['results'][0]
                distance = int(result_data.get('distance', 0))
                duration = int(result_data.get('duration', 0))
                result = (distance, duration)

                # 写入缓存（元组转列表）
                if self.cache:
                    self.cache.set('distance', cache_key, list(result))

                return result

            return 0, 0

        except Exception as e:
            logger.error(f"Error getting distance: {str(e)}")
            return 0, 0

    def get_walking_route(
        self,
        origin: str,
        destination: str
    ) -> Tuple[int, int, str]:
        """
        获取步行路线。

        Args:
            origin: 起点坐标 "lng,lat"
            destination: 终点坐标 "lng,lat"

        Returns:
            Tuple[int, int, str]: (距离(米), 时间(秒), polyline字符串)
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_walking_route',
                origin=origin,
                destination=destination
            )
            cached_result = self.cache.get('route', cache_key)
            if cached_result is not None:
                return tuple(cached_result) if isinstance(cached_result, list) else cached_result

        try:
            params = {
                'key': self.api_key,
                'origin': origin,
                'destination': destination
            }

            response = requests.get(
                "https://restapi.amap.com/v3/direction/walking",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('route', {}).get('paths'):
                path = data['route']['paths'][0]
                distance = int(path.get('distance', 0))
                duration = int(path.get('duration', 0))

                # 提取polyline
                steps = path.get('steps', [])
                polylines = [step.get('polyline') for step in steps if step.get('polyline')]
                polyline = ";".join(polylines)

                result = (distance, duration, polyline)

                # 写入缓存（元组转列表）
                if self.cache:
                    self.cache.set('route', cache_key, list(result))

                return result

            return 0, 0, ""

        except Exception as e:
            logger.error(f"Error getting walking route: {str(e)}")
            return 0, 0, ""

    def get_transit_route(
        self,
        origin: str,
        destination: str,
        city: str
    ) -> Tuple[int, int, str]:
        """
        获取公交/地铁路线。

        Args:
            origin: 起点坐标 "lng,lat"
            destination: 终点坐标 "lng,lat"
            city: 城市名称

        Returns:
            Tuple[int, int, str]: (距离(米), 时间(秒), polyline字符串)
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_transit_route',
                origin=origin,
                destination=destination,
                city=city
            )
            cached_result = self.cache.get('route', cache_key)
            if cached_result is not None:
                return tuple(cached_result) if isinstance(cached_result, list) else cached_result

        try:
            params = {
                'key': self.api_key,
                'origin': origin,
                'destination': destination,
                'city': city,
                'extensions': 'base'
            }

            response = requests.get(
                "https://restapi.amap.com/v3/direction/transit/integrated",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('route', {}).get('transits'):
                transit = data['route']['transits'][0]
                distance = int(transit.get('distance', 0))
                duration = int(transit.get('duration', 0))

                # 提取polyline
                segments = transit.get('segments', [])
                polylines = []

                for segment in segments:
                    # 步行polyline
                    walk_steps = segment.get('walking', {}).get('steps', [])
                    walk_polylines = [step.get('polyline') for step in walk_steps if step.get('polyline')]
                    polylines.extend(walk_polylines)

                    # 公交/地铁polyline
                    if segment.get('bus'):
                        bus_steps = segment['bus'].get('buslines', [])
                        if bus_steps:
                            bus_polyline = bus_steps[0].get('polyline')
                            if bus_polyline:
                                polylines.append(bus_polyline)

                polyline = ";".join(polylines)
                result = (distance, duration, polyline)

                # 写入缓存（元组转列表）
                if self.cache:
                    self.cache.set('route', cache_key, list(result))

                return result

            return 0, 0, ""

        except Exception as e:
            logger.error(f"Error getting transit route: {str(e)}")
            return 0, 0, ""

    def get_driving_route(
        self,
        origin: str,
        destination: str,
        waypoints: str = '',
        strategy: int = 0
    ) -> Tuple[int, int, str]:
        """
        获取驾车路线。

        Args:
            origin: 起点坐标 "lng,lat"
            destination: 终点坐标 "lng,lat"
            waypoints: 途经点，多个用'|'分隔
            strategy: 路线策略（0:最快, 1:最短, 2:避免拥堵）

        Returns:
            Tuple[int, int, str]: (距离(米), 时间(秒), polyline字符串)
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_driving_route',
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                strategy=strategy
            )
            cached_result = self.cache.get('route', cache_key)
            if cached_result is not None:
                return tuple(cached_result) if isinstance(cached_result, list) else cached_result

        try:
            params = {
                'key': self.api_key,
                'origin': origin,
                'destination': destination,
                'strategy': strategy
            }
            if waypoints:
                params['waypoints'] = waypoints

            response = requests.get(
                "https://restapi.amap.com/v3/direction/driving",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('route', {}).get('paths'):
                path = data['route']['paths'][0]
                distance = int(path.get('distance', 0))
                duration = int(path.get('duration', 0))

                # 提取polyline
                steps = path.get('steps', [])
                polylines = [step.get('polyline') for step in steps if step.get('polyline')]
                polyline = ";".join(polylines)

                result = (distance, duration, polyline)

                # 写入缓存（元组转列表）
                if self.cache:
                    self.cache.set('route', cache_key, list(result))

                return result

            return 0, 0, ""

        except Exception as e:
            logger.error(f"Error getting driving route: {str(e)}")
            return 0, 0, ""

    def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """
        获取城市天气信息。

        Args:
            city: 城市名称

        Returns:
            Optional[Dict]: 天气数据，失败返回None
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_weather',
                city=city
            )
            cached_result = self.cache.get('weather', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            params = {
                'key': self.api_key,
                'city': city,
                'extensions': 'all',
                'output': 'json'
            }

            response = requests.get(
                "https://restapi.amap.com/v3/weather/weatherInfo",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1':
                # 写入缓存
                if self.cache:
                    self.cache.set('weather', cache_key, data)

                return data

            return None

        except Exception as e:
            logger.error(f"Error getting weather for {city}: {str(e)}")
            return None

    def search_around(
        self,
        location: str,
        keywords: str = '',
        radius: int = 1000,
        poi_type: str = '',
        offset: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        周边搜索POI。

        Args:
            location: 中心点坐标 "lng,lat"
            keywords: 关键词
            radius: 搜索半径（米）
            poi_type: POI类型
            offset: 返回数量
            page: 页码

        Returns:
            List[Dict]: POI列表
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='search_around',
                location=location,
                keywords=keywords,
                radius=radius,
                poi_type=poi_type,
                offset=offset,
                page=page
            )
            cached_result = self.cache.get('poi_search', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            params = {
                'key': self.api_key,
                'location': location,
                'keywords': keywords,
                'types': poi_type,
                'radius': radius,
                'offset': offset,
                'page': page,
                'extensions': 'all'
            }

            response = requests.get(
                "https://restapi.amap.com/v3/place/around",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            result = data.get('pois', [])

            # 写入缓存
            if self.cache:
                self.cache.set('poi_search', cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error searching around {location}: {str(e)}")
            return []

    def get_poi_detail(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """
        获取POI详细信息。

        Args:
            poi_id: POI ID

        Returns:
            Optional[Dict]: POI详细信息，失败返回None
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_poi_detail',
                poi_id=poi_id
            )
            cached_result = self.cache.get('poi_gates', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            params = {
                'key': self.api_key,
                'id': poi_id
            }

            response = requests.get(
                "https://restapi.amap.com/v3/place/detail",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1' and data.get('pois'):
                result = data['pois'][0]

                # 写入缓存
                if self.cache:
                    self.cache.set('poi_gates', cache_key, result)

                return result

            return None

        except Exception as e:
            logger.error(f"Error getting POI detail for {poi_id}: {str(e)}")
            return None

    def get_distance_batch(
        self,
        origins: List[str],
        destination: str,
        dist_type: str = '1'
    ) -> List[Tuple[int, int]]:
        """
        批量获取距离和时间。

        Args:
            origins: 起点坐标列表，每个元素格式 "lng,lat"
            destination: 终点坐标 "lng,lat"
            dist_type: 距离类型（1:直线距离, 0:驾车导航距离）

        Returns:
            List[Tuple[int, int]]: (距离(米), 时间(秒))列表
        """
        # AMap API支持批量查询，最多10个起点
        # 将origins按10个一组分批
        results = []
        batch_size = 10

        for i in range(0, len(origins), batch_size):
            batch = origins[i:i + batch_size]
            origins_str = '|'.join(batch)

            # 检查缓存
            cache_key = None
            if self.cache:
                cache_key = self.cache._generate_key(
                    method='get_distance_batch',
                    origins=origins_str,
                    destination=destination,
                    dist_type=dist_type
                )
                cached_result = self.cache.get('distance', cache_key)
                if cached_result is not None:
                    # 缓存的是列表的列表，需要转回元组列表
                    results.extend([tuple(r) if isinstance(r, list) else r for r in cached_result])
                    continue

            try:
                params = {
                    'key': self.api_key,
                    'origins': origins_str,
                    'destination': destination,
                    'type': dist_type
                }

                response = requests.get(
                    "https://restapi.amap.com/v3/distance",
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                batch_results = []
                if data.get('status') == '1' and data.get('results'):
                    for result_data in data['results']:
                        distance = int(result_data.get('distance', 0))
                        duration = int(result_data.get('duration', 0))
                        batch_results.append((distance, duration))
                else:
                    # 失败时填充默认值
                    batch_results = [(0, 0)] * len(batch)

                results.extend(batch_results)

                # 写入缓存（元组转列表）
                if self.cache and cache_key:
                    self.cache.set('distance', cache_key, [list(r) for r in batch_results])

            except Exception as e:
                logger.error(f"Error getting batch distance: {str(e)}")
                # 失败时填充默认值
                results.extend([(0, 0)] * len(batch))

        return results

    def get_poi_gates(
        self,
        poi_name: str,
        city: str,
        search_radius: int = 2000
    ) -> Dict[str, Any]:
        """
        获取POI的所有出入口/门信息。

        这是多出入口优化的核心方法。它会：
        1. 搜索主POI获取中心坐标
        2. 在该坐标周围搜索所有包含"门|出入口|入口|出口"的POI
        3. 返回主POI信息和所有门的信息

        Args:
            poi_name: POI名称
            city: 城市名称
            search_radius: 搜索半径（米），默认2000米

        Returns:
            Dict包含：
            {
                'main_poi': {主POI信息},
                'gates': [门列表],
                'has_multiple_gates': bool  # 是否有多个门（>1）
            }
        """
        # 检查缓存
        if self.cache:
            cache_key = self.cache._generate_key(
                method='get_poi_gates',
                poi_name=poi_name,
                city=city,
                search_radius=search_radius
            )
            cached_result = self.cache.get('poi_gates', cache_key)
            if cached_result is not None:
                return cached_result

        try:
            # Step 1: 搜索主POI
            main_pois = self.search_pois(
                city=city,
                keywords=poi_name,
                offset=1
            )

            if not main_pois:
                logger.warning(f"Main POI not found: {poi_name} in {city}")
                result = {
                    'main_poi': None,
                    'gates': [],
                    'has_multiple_gates': False
                }
                # 写入缓存
                if self.cache:
                    self.cache.set('poi_gates', cache_key, result)
                return result

            main_poi = main_pois[0]
            main_location = main_poi.get('location', '')

            if not main_location:
                logger.warning(f"Main POI has no location: {poi_name}")
                result = {
                    'main_poi': main_poi,
                    'gates': [],
                    'has_multiple_gates': False
                }
                # 写入缓存
                if self.cache:
                    self.cache.set('poi_gates', cache_key, result)
                return result

            # Step 2: 搜索周边的门/出入口
            # 使用多个关键词组合搜索，确保找到所有可能的门
            gate_keywords = ['门', '出入口', '入口', '出口', 'gate', 'entrance', 'exit']
            all_gates = []
            seen_locations = set()  # 去重，避免重复的门

            for keyword in gate_keywords:
                gates = self.search_around(
                    location=main_location,
                    keywords=keyword,
                    radius=search_radius,
                    offset=50  # 每个关键词最多50个结果
                )

                for gate in gates:
                    gate_location = gate.get('location', '')
                    # 去重：相同坐标的门只保留一个
                    if gate_location and gate_location not in seen_locations:
                        seen_locations.add(gate_location)
                        all_gates.append(gate)

            # Step 3: 过滤门 - 确保门的名称包含主POI名称或相关关键词
            # 这避免了搜索到无关的POI
            filtered_gates = []
            main_poi_name_clean = main_poi.get('name', '').strip()

            for gate in all_gates:
                gate_name = gate.get('name', '')
                # 门应该包含主POI名称，或者是明确的门/入口/出口
                if (main_poi_name_clean in gate_name or
                    any(kw in gate_name for kw in ['门', '入口', '出口', '出入口', 'gate', 'entrance', 'exit'])):
                    filtered_gates.append(gate)

            # 如果过滤后没有门，则使用主POI坐标作为唯一"门"
            if not filtered_gates:
                logger.info(f"No gates found for {poi_name}, using main POI location")
                filtered_gates = [{
                    'id': main_poi.get('id', ''),
                    'name': main_poi.get('name', '') + '(主入口)',
                    'location': main_location,
                    'address': main_poi.get('address', ''),
                    'is_main': True
                }]

            result = {
                'main_poi': main_poi,
                'gates': filtered_gates,
                'has_multiple_gates': len(filtered_gates) > 1
            }

            # 写入缓存
            if self.cache:
                self.cache.set('poi_gates', cache_key, result)

            logger.info(f"Found {len(filtered_gates)} gate(s) for {poi_name}")
            return result

        except Exception as e:
            logger.error(f"Error getting gates for {poi_name}: {str(e)}")
            result = {
                'main_poi': None,
                'gates': [],
                'has_multiple_gates': False
            }
            return result
