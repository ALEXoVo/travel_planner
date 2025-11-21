"""
高德地图API服务模块

封装所有与高德地图API交互的功能，包括POI搜索、地理编码、
路径规划、天气查询等。
"""
import requests
from typing import Dict, List, Tuple, Optional, Any
import logging
from config import Config

logger = logging.getLogger(__name__)


class AmapService:
    """高德地图API服务类"""

    def __init__(self, api_key: str = None, timeout: int = None):
        """
        初始化高德地图服务。

        Args:
            api_key: 高德地图API密钥，默认从配置读取
            timeout: 请求超时时间（秒），默认从配置读取
        """
        self.api_key = api_key or Config.AMAP_API_KEY
        self.timeout = timeout or Config.AMAP_TIMEOUT

        if not self.api_key:
            logger.warning("AMap API key not configured")

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

            return data.get('pois', [])

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
                return lng, lat

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
                return data.get('regeocode', {})

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
                result = data['results'][0]
                distance = int(result.get('distance', 0))
                duration = int(result.get('duration', 0))
                return distance, duration

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

                return distance, duration, polyline

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
                return distance, duration, polyline

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

                return distance, duration, polyline

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
                return data

            return None

        except Exception as e:
            logger.error(f"Error getting weather for {city}: {str(e)}")
            return None
