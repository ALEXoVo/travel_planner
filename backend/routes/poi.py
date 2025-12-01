"""
POI管理路由模块

处理用户自定义POI的添加、管理和路径优化功能。
支持POI搜索、用户POI列表管理、路径优化等。
"""
from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime

from services.route_optimizer import RouteOptimizer
from services.amap_service import AmapService

logger = logging.getLogger(__name__)

# 创建Blueprint
poi_bp = Blueprint('poi', __name__)


# ==================== 1. POI搜索自动补全 ====================
@poi_bp.route('/api/poi/autocomplete', methods=['GET'])
def autocomplete_poi():
    """
    POI搜索自动补全

    Query参数:
        query: 搜索关键词 (必需)
        city: 城市名称 (必需)
        limit: 返回数量限制 (可选, 默认10)

    Returns:
        {
            "suggestions": [
                {
                    "id": "POI ID",
                    "name": "名称",
                    "address": "地址",
                    "location": "lng,lat",
                    "type": "类型",
                    "rating": "评分"
                }
            ],
            "count": 10
        }
    """
    try:
        query = request.args.get('query', '').strip()
        city = request.args.get('city', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query or not city:
            return jsonify({"error": "query and city are required"}), 400

        # 复用现有的amap_service
        amap_service = AmapService()
        results = amap_service.search_pois(
            city=city,
            keywords=query,
            poi_type='',  # 不限制类型
            offset=limit
        )

        # 格式化返回数据
        suggestions = []
        for poi in results[:limit]:
            suggestions.append({
                'id': poi.get('id'),
                'name': poi.get('name'),
                'address': poi.get('address', ''),
                'location': poi.get('location', ''),
                'type': poi.get('type', ''),
                'rating': poi.get('biz_ext', {}).get('rating', '')
            })

        return jsonify({
            "suggestions": suggestions,
            "count": len(suggestions)
        })

    except Exception as e:
        logger.error(f"POI autocomplete error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 2. 添加POI到用户列表 ====================
@poi_bp.route('/api/user-pois/add', methods=['POST'])
def add_user_poi():
    """
    添加POI到用户选择列表（Session）

    Request Body:
        {
            "poi": {
                "id": "POI ID",
                "name": "名称",
                "address": "地址",
                "location": "lng,lat",
                "type": "类型"
            },
            "city": "城市"
        }
    """
    try:
        data = request.get_json()
        poi = data.get('poi')
        city = data.get('city')

        if not poi or not city:
            return jsonify({"error": "poi and city are required"}), 400

        # 初始化Session结构
        if 'user_selected_pois' not in session:
            session['user_selected_pois'] = {
                'destination_city': city,
                'pois': []
            }

        user_data = session['user_selected_pois']

        # 城市一致性检查
        if user_data['destination_city'] != city:
            return jsonify({
                "error": f"Cannot mix POIs from different cities. Current city: {user_data['destination_city']}"
            }), 400

        # POI去重检查
        existing_ids = [p['id'] for p in user_data['pois']]
        if poi['id'] in existing_ids:
            return jsonify({"error": "POI already in the list"}), 409

        # 解析坐标
        location_str = poi.get('location', '')
        if ',' in location_str:
            lng, lat = location_str.split(',')
            poi['lng'] = float(lng)
            poi['lat'] = float(lat)

        # 添加时间戳
        poi['added_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 添加到Session
        user_data['pois'].append(poi)
        session['user_selected_pois'] = user_data
        session.modified = True  # 标记Session已修改

        return jsonify({
            "message": "POI added successfully",
            "total_count": len(user_data['pois'])
        })

    except Exception as e:
        logger.error(f"Add POI error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 3. 获取用户POI列表 ====================
@poi_bp.route('/api/user-pois/list', methods=['GET'])
def list_user_pois():
    """获取当前用户选择的POI列表"""
    user_data = session.get('user_selected_pois', {})

    return jsonify({
        "destination_city": user_data.get('destination_city', ''),
        "pois": user_data.get('pois', []),
        "count": len(user_data.get('pois', []))
    })


# ==================== 4. 移除单个POI ====================
@poi_bp.route('/api/user-pois/remove/<poi_id>', methods=['DELETE'])
def remove_user_poi(poi_id):
    """移除指定POI"""
    try:
        if 'user_selected_pois' not in session:
            return jsonify({"error": "No POIs in session"}), 404

        user_data = session['user_selected_pois']
        original_count = len(user_data['pois'])

        # 过滤掉指定POI
        user_data['pois'] = [p for p in user_data['pois'] if p['id'] != poi_id]

        if len(user_data['pois']) == original_count:
            return jsonify({"error": "POI not found"}), 404

        session['user_selected_pois'] = user_data
        session.modified = True

        return jsonify({
            "message": "POI removed successfully",
            "remaining_count": len(user_data['pois'])
        })

    except Exception as e:
        logger.error(f"Remove POI error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 5. 清空POI列表 ====================
@poi_bp.route('/api/user-pois/clear', methods=['DELETE'])
def clear_user_pois():
    """清空所有用户选择的POI"""
    session.pop('user_selected_pois', None)
    session.modified = True

    return jsonify({"message": "All POIs cleared"})


@poi_bp.route('/api/poi/optimize', methods=['POST'])
def optimize_poi_route():
    """
    优化用户选择的POI访问路线。

    Request Body:
        {
            "pois": [POI列表],
            "start_location": {"lng": 经度, "lat": 纬度},
            "preferences": {
                "consider_weather": true,
                "consider_traffic": true
            }
        }

    Returns:
        JSON: 优化后的路线

    Note:
        这是核心功能！使用OR-Tools进行路径优化。
        后续实现时，这里会调用route_optimizer服务。
    """
    try:
        data = request.get_json(force=True)
        pois = data.get('pois', [])
        start_location = data.get('start_location', {})

        if not pois:
            return jsonify({"error": "No POIs provided"}), 400

        # 提取起点坐标
        start_lng = start_location.get('lng')
        start_lat = start_location.get('lat')

        if start_lng is None or start_lat is None:
            return jsonify({"error": "Invalid start location"}), 400

        # 初始化路径优化器
        optimizer = RouteOptimizer()

        # 执行路径优化
        logger.info(f"Optimizing route for {len(pois)} POIs")
        optimized_route = optimizer.optimize_route(
            pois=pois,
            start_location=(start_lng, start_lat)
        )

        # 重新排序POI列表
        from services.route_optimizer import reorder_pois
        optimized_pois = reorder_pois(pois, optimized_route)

        return jsonify({
            "status": "success",
            "optimized_route": optimized_route,
            "optimized_pois": optimized_pois,
            "message": "路径优化成功"
        })

    except Exception as e:
        logger.error(f"Optimize route error: {str(e)}")
        return jsonify({
            "error": f"路径优化失败: {str(e)}"
        }), 500


@poi_bp.route('/api/poi/delete', methods=['DELETE'])
def delete_poi():
    """
    删除用户添加的POI。

    Request Body:
        {
            "poi_id": "POI ID"
        }

    Returns:
        JSON: 删除结果
    """
    try:
        # TODO: 实现POI删除逻辑
        return jsonify({
            "message": "POI管理功能暂未实现，敬请期待",
            "status": "pending_implementation"
        }), 501

    except Exception as e:
        logger.error(f"Delete POI error: {str(e)}")
        return jsonify({"error": str(e)}), 500
