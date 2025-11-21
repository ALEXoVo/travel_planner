"""
地理计算工具模块

提供地理编码、坐标解析、距离计算等地理相关的工具函数。
"""
import requests
from typing import Tuple, Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_poi_coordinates(
    name: str,
    address: str,
    city: str,
    amap_key: str
) -> Tuple[Optional[float], Optional[float]]:
    """
    通过地理编码或POI搜索获取坐标。

    优先使用地理编码（将名称和地址合并），如果失败则回退到POI文本搜索。

    Args:
        name: POI名称
        address: POI地址
        city: 所在城市
        amap_key: 高德地图API密钥

    Returns:
        Tuple[Optional[float], Optional[float]]: (经度, 纬度)，失败返回(None, None)

    Examples:
        >>> lng, lat = get_poi_coordinates("天安门", "东城区", "北京", "your_key")
        >>> print(f"{lng}, {lat}")
        116.397428, 39.90923
    """
    # 优先使用地理编码，将名称和地址合并，提高准确率
    full_address = f"{name}, {address}" if address else name

    try:
        # 1. 标准地理编码
        geo_params = {
            'key': amap_key,
            'address': full_address,
            'city': city
        }
        geo_response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params=geo_params,
            timeout=5
        )
        geo_data = geo_response.json()

        if geo_data.get('status') == '1' and geo_data.get('geocodes'):
            location_str = geo_data['geocodes'][0]['location']
            if location_str:
                lng, lat = map(float, location_str.split(','))
                return lng, lat

    except Exception as e:
        logger.warning(f"Geocode failed for {name}: {str(e)}")

    # 2. Fallback: POI 文本搜索 (使用名称)
    try:
        text_search_params = {
            "key": amap_key,
            "keywords": name,
            "city": city,
            "citylimit": "true",
            "offset": 1
        }
        text_search_response = requests.get(
            "https://restapi.amap.com/v3/place/text",
            params=text_search_params,
            timeout=5
        )
        text_search_data = text_search_response.json()

        if text_search_data.get('status') == '1' and text_search_data.get('pois'):
            poi_location_str = text_search_data['pois'][0].get('location')
            if poi_location_str:
                lng, lat = map(float, poi_location_str.split(','))
                return lng, lat

    except Exception as e:
        logger.warning(f"POI Search failed for {name}: {str(e)}")

    return None, None


def add_coordinates_to_pois(
    poi_list: List[Dict[str, Any]],
    city: str,
    amap_key: str
) -> None:
    """
    批量为POI列表中的每个POI添加'lng'和'lat'坐标字段。

    直接修改传入的poi_list，为每个POI字典添加坐标信息。

    Args:
        poi_list: POI列表，每个元素为包含POI信息的字典
        city: 所在城市
        amap_key: 高德地图API密钥

    Examples:
        >>> pois = [{'name': '天安门', 'address': '东城区'}]
        >>> add_coordinates_to_pois(pois, '北京', 'your_key')
        >>> print(pois[0]['lng'], pois[0]['lat'])
        116.397428 39.90923
    """
    for poi in poi_list:
        if 'location' in poi and poi['location']:
            try:
                # 如果 POI 数据自带 location (lng,lat 格式)
                lng, lat = map(float, poi['location'].split(','))
                poi['lng'] = lng
                poi['lat'] = lat
            except Exception:
                # 如果 location 格式不正确，尝试通过名称和地址获取
                name = poi.get('name', '')
                address = poi.get('address', '')
                lng, lat = get_poi_coordinates(name, address, city, amap_key)
                poi['lng'] = lng
                poi['lat'] = lat
        else:
            # 如果没有 location 字段，尝试通过名称和地址获取
            name = poi.get('name', '')
            address = poi.get('address', '')
            lng, lat = get_poi_coordinates(name, address, city, amap_key)
            poi['lng'] = lng
            poi['lat'] = lat


def parse_location_string(location_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    解析位置字符串为经纬度。

    Args:
        location_str: 位置字符串，格式为 "lng,lat"

    Returns:
        Tuple[Optional[float], Optional[float]]: (经度, 纬度)，失败返回(None, None)

    Examples:
        >>> parse_location_string("116.397428,39.90923")
        (116.397428, 39.90923)
    """
    try:
        lng, lat = map(float, location_str.split(','))
        return lng, lat
    except Exception as e:
        logger.error(f"Failed to parse location string '{location_str}': {str(e)}")
        return None, None


def calculate_distance(
    lng1: float,
    lat1: float,
    lng2: float,
    lat2: float
) -> float:
    """
    计算两个坐标点之间的直线距离（Haversine公式）。

    Args:
        lng1: 起点经度
        lat1: 起点纬度
        lng2: 终点经度
        lat2: 终点纬度

    Returns:
        float: 距离（米）

    Examples:
        >>> distance = calculate_distance(116.397428, 39.90923, 116.407428, 39.91923)
        >>> print(f"{distance:.2f}m")
        1234.56m
    """
    from math import radians, sin, cos, sqrt, atan2

    # 地球半径（米）
    R = 6371000

    # 转换为弧度
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)

    # Haversine公式
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def format_coordinates(lng: float, lat: float) -> str:
    """
    格式化坐标为高德API所需的字符串格式。

    Args:
        lng: 经度
        lat: 纬度

    Returns:
        str: 格式化后的坐标字符串 "lng,lat"

    Examples:
        >>> format_coordinates(116.397428, 39.90923)
        '116.397428,39.90923'
    """
    return f"{lng},{lat}"
