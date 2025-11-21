"""
地图相关路由模块

处理路径规划、天气查询等地图功能的API端点。
"""
from flask import Blueprint, request, jsonify
import logging

from services.amap_service import AmapService

logger = logging.getLogger(__name__)

# 创建Blueprint
map_bp = Blueprint('map', __name__)


@map_bp.route('/api/route/planning', methods=['POST'])
def route_planning():
    """
    路径规划接口。

    Request Body:
        {
            "origin": "起点坐标 lng,lat",
            "destination": "终点坐标 lng,lat",
            "waypoints": ["途经点坐标"],
            "strategy": 路线策略（0:最快, 1:最短, 2:避免拥堵）
        }

    Returns:
        JSON: 高德地图API返回的路径规划结果
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        origin = data.get('origin')
        destination = data.get('destination')
        waypoints = data.get('waypoints', [])
        strategy = data.get('strategy', 0)

        if not origin or not destination:
            return jsonify({"error": "Missing origin or destination"}), 400

        logger.info(f"Planning route from {origin} to {destination}")

        # 初始化高德服务
        amap_service = AmapService()

        # 获取驾车路线
        waypoints_str = '|'.join(waypoints) if waypoints else ''
        distance, duration, polyline = amap_service.get_driving_route(
            origin=origin,
            destination=destination,
            waypoints=waypoints_str,
            strategy=strategy
        )

        if distance == 0:
            return jsonify({"error": "Route planning failed"}), 500

        # 构建响应（模拟高德API格式）
        response_data = {
            "status": "1",
            "route": {
                "paths": [{
                    "distance": str(distance),
                    "duration": str(duration),
                    "polyline": polyline
                }]
            }
        }

        logger.info("Route planning successful")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Route planning error: {str(e)}")
        return jsonify({
            "error": f"路径规划失败: {str(e)}"
        }), 500


@map_bp.route('/api/weather/info', methods=['GET'])
def weather_info():
    """
    获取天气信息接口。

    Query Parameters:
        city: 城市名称

    Returns:
        JSON: 天气数据
    """
    try:
        city = request.args.get('city')

        if not city:
            return jsonify({"error": "Missing city parameter"}), 400

        logger.info(f"Fetching weather info for city: {city}")

        # 初始化高德服务
        amap_service = AmapService()

        # 获取天气
        weather_data = amap_service.get_weather(city)

        if not weather_data:
            return jsonify({"error": "Failed to fetch weather data"}), 500

        logger.info("Weather info fetched successfully")
        return jsonify(weather_data)

    except Exception as e:
        logger.error(f"Weather info error: {str(e)}")
        return jsonify({
            "error": f"获取天气信息失败: {str(e)}"
        }), 500
