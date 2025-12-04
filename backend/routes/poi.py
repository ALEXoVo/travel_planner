"""
POI管理路由模块

处理用户自定义POI的添加、管理和路径优化功能。
支持POI搜索、用户POI列表管理、路径优化等。
"""
from flask import Blueprint, request, jsonify, session
from flask_login import current_user
import logging
from datetime import datetime
import json

from models import db
from models.poi import UserPOIFavorite
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
        keywords: 搜索关键词 (必需) - 兼容前端参数名
        query: 搜索关键词 (必需) - 向后兼容
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
        # 兼容 keywords 和 query 两种参数名
        query = request.args.get('keywords', '').strip() or request.args.get('query', '').strip()
        city = request.args.get('city', '').strip()
        limit = int(request.args.get('limit', 10))

        if not query or not city:
            return jsonify({"error": "keywords and city are required"}), 400

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
    添加POI到用户选择列表（兼容模式：DB/Session）

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

        # 新增：接收source、priority和itinerary_id参数
        source = data.get('source', 'user')  # 默认'user'（用户添加）
        priority = data.get('priority', 'must_visit')  # 默认'must_visit'（必去）
        itinerary_id = data.get('itinerary_id', None)  # 可选

        if not poi or not city:
            return jsonify({"error": "poi and city are required"}), 400

        # 解析坐标
        location_str = poi.get('location', '')
        if ',' in location_str:
            lng, lat = location_str.split(',')
            poi['lng'] = float(lng)
            poi['lat'] = float(lat)
        else:
            poi['lng'] = None
            poi['lat'] = None

        # 🆕 已登录用户：保存到数据库
        if current_user.is_authenticated:
            logger.info(f"[ADD POI] Authenticated user: user_id={current_user.id}, username={current_user.username}, city={city}, poi_id={poi['id']}, priority={priority}")
            try:
                # POI去重检查
                existing = UserPOIFavorite.query.filter_by(
                    user_id=current_user.id,
                    destination_city=city,
                    poi_id=poi['id']
                ).first()

                if existing:
                    logger.warning(f"[ADD POI] POI already exists: user_id={current_user.id}, poi_id={poi['id']}")
                    return jsonify({"error": "POI already in the list"}), 409

                # 创建数据库记录（包含新字段）
                favorite = UserPOIFavorite(
                    user_id=current_user.id,
                    destination_city=city,
                    poi_name=poi.get('name'),
                    poi_id=poi.get('id'),
                    location=json.dumps({'lng': poi.get('lng'), 'lat': poi.get('lat')}),
                    poi_type=poi.get('type'),
                    source=source,  # 新增
                    priority=priority,  # 新增
                    itinerary_id=itinerary_id  # 新增
                )
                db.session.add(favorite)
                db.session.commit()
                logger.info(f"[ADD POI] DB commit successful: poi_id={poi['id']}")

                # 查询当前总数
                total_count = UserPOIFavorite.query.filter_by(
                    user_id=current_user.id,
                    destination_city=city
                ).count()

                logger.info(f"[ADD POI] POI saved to DB: user={current_user.username}, poi={poi.get('name')}, total_count={total_count}")

                return jsonify({
                    "message": "POI added successfully",
                    "total_count": total_count
                })

            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to save POI to DB: {str(e)}")
                return jsonify({'error': 'Failed to save POI'}), 500

        # 未登录用户：保存到Session（原有逻辑）
        else:
            # 诊断：打印Session ID
            from flask import request as flask_request
            logger.info(f"[ADD POI] Session ID: {session.get('_id', 'NO SESSION ID')}")
            logger.info(f"[ADD POI] Session SID cookie: {flask_request.cookies.get('travelplanner_session', 'NO COOKIE')}")
            logger.info(f"[ADD POI] Unauthenticated user: using session storage, city={city}, poi_id={poi['id']}, priority={priority}")
            # 初始化Session结构
            if 'user_selected_pois' not in session:
                session['user_selected_pois'] = {
                    'destination_city': city,
                    'pois': []
                }
                logger.info(f"[ADD POI] Initialized new session storage for city={city}")

            user_data = session['user_selected_pois']

            # 城市一致性检查
            if user_data['destination_city'] != city:
                logger.warning(f"[ADD POI] City mismatch: session_city={user_data['destination_city']}, new_city={city}")
                return jsonify({
                    "error": f"Cannot mix POIs from different cities. Current city: {user_data['destination_city']}"
                }), 400

            # POI去重检查
            existing_ids = [p['id'] for p in user_data['pois']]
            if poi['id'] in existing_ids:
                logger.warning(f"[ADD POI] POI already exists in session: poi_id={poi['id']}")
                return jsonify({"error": "POI already in the list"}), 409

            # 添加时间戳和新字段
            poi['added_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            poi['source'] = source  # 新增
            poi['priority'] = priority  # 新增

            # 添加到Session
            user_data['pois'].append(poi)
            session['user_selected_pois'] = user_data
            session.modified = True  # 标记Session已修改

            logger.info(f"[ADD POI] POI saved to session: poi={poi.get('name')}, total_count={len(user_data['pois'])}")

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
    """
    获取当前用户选择的POI列表（兼容模式：DB/Session）

    Query参数:
        city: 城市名称（可选，用于数据库查询）
    """
    try:
        city = request.args.get('city', '').strip()
        logger.info(f"[LIST POI] Request received: city={city if city else 'all'}")

        # 🆕 已登录用户：从数据库读取
        if current_user.is_authenticated:
            logger.info(f"[LIST POI] Authenticated user: user_id={current_user.id}, username={current_user.username}")
            # 如果提供了city参数，按城市过滤；否则返回所有POI
            if city:
                favorites = UserPOIFavorite.query.filter_by(
                    user_id=current_user.id,
                    destination_city=city
                ).order_by(UserPOIFavorite.created_at.desc()).all()
                logger.info(f"[LIST POI] DB query with city filter: found {len(favorites)} POIs")
            else:
                # 返回该用户的所有POI，不限城市
                favorites = UserPOIFavorite.query.filter_by(
                    user_id=current_user.id
                ).order_by(UserPOIFavorite.created_at.desc()).all()
                logger.info(f"[LIST POI] DB query without city filter: found {len(favorites)} POIs")

            # 转换为前端期望的格式（包含priority和source字段）
            pois = []
            for fav in favorites:
                location_data = json.loads(fav.location) if fav.location else {}
                pois.append({
                    'poi_id': fav.poi_id,  # 使用poi_id而非id，匹配前端
                    'poi_name': fav.poi_name,  # 使用poi_name而非name，匹配前端
                    'id': fav.poi_id,  # 兼容性：同时保留id字段
                    'name': fav.poi_name,  # 兼容性：同时保留name字段
                    'city': fav.destination_city,
                    'lng': location_data.get('lng'),
                    'lat': location_data.get('lat'),
                    'type': fav.poi_type,
                    'added_at': fav.created_at.isoformat(),
                    'priority': fav.priority,  # 新增：优先级字段
                    'source': fav.source  # 新增：来源字段
                })

            logger.info(f"[LIST POI] Returning {len(pois)} POIs for authenticated user")
            return jsonify({
                "destination_city": city if city else "all",
                "pois": pois,
                "count": len(pois)
            })

        # 未登录用户：从Session读取（原有逻辑）
        else:
            # 诊断：打印Session ID
            from flask import request as flask_request
            logger.info(f"[LIST POI] Session ID: {session.get('_id', 'NO SESSION ID')}")
            logger.info(f"[LIST POI] Session SID cookie: {flask_request.cookies.get('travelplanner_session', 'NO COOKIE')}")
            logger.info(f"[LIST POI] Unauthenticated user: reading from session")
            logger.info(f"[LIST POI] Session keys: {list(session.keys())}")
            user_data = session.get('user_selected_pois', {})
            pois = user_data.get('pois', [])
            logger.info(f"[LIST POI] Session data: destination_city={user_data.get('destination_city', 'none')}, count={len(pois)}")

            return jsonify({
                "destination_city": user_data.get('destination_city', ''),
                "pois": pois,
                "count": len(pois)
            })

    except Exception as e:
        logger.error(f"List user POIs error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 4. 移除单个POI ====================
@poi_bp.route('/api/user-pois/remove/<poi_id>', methods=['DELETE'])
def remove_user_poi(poi_id):
    """
    移除指定POI（兼容模式：DB/Session）
    """
    try:
        # 🆕 已登录用户：从数据库删除
        if current_user.is_authenticated:
            # 直接用poi_id查找，不需要city参数
            favorite = UserPOIFavorite.query.filter_by(
                user_id=current_user.id,
                poi_id=poi_id
            ).first()

            if not favorite:
                return jsonify({"error": "POI not found"}), 404

            db.session.delete(favorite)
            db.session.commit()

            # 查询剩余总数量
            remaining_count = UserPOIFavorite.query.filter_by(
                user_id=current_user.id
            ).count()

            logger.info(f"POI deleted from DB: user={current_user.username}, poi_id={poi_id}")

            return jsonify({
                "message": "POI removed successfully",
                "remaining_count": remaining_count
            })

        # 未登录用户：从Session删除（原有逻辑）
        else:
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
        db.session.rollback()
        logger.error(f"Remove POI error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 5. 清空POI列表 ====================
@poi_bp.route('/api/user-pois/clear', methods=['DELETE'])
def clear_user_pois():
    """
    清空所有用户选择的POI（兼容模式：DB/Session）

    Query参数:
        city: 城市名称（已登录用户必需）
    """
    try:
        city = request.args.get('city', '').strip()

        # 🆕 已登录用户：从数据库删除
        if current_user.is_authenticated:
            if not city:
                return jsonify({"error": "city parameter required"}), 400

            deleted_count = UserPOIFavorite.query.filter_by(
                user_id=current_user.id,
                destination_city=city
            ).delete()
            db.session.commit()

            logger.info(f"All POIs cleared from DB: user={current_user.username}, city={city}, count={deleted_count}")

            return jsonify({
                "message": "All POIs cleared",
                "deleted_count": deleted_count
            })

        # 未登录用户：从Session删除（原有逻辑）
        else:
            session.pop('user_selected_pois', None)
            session.modified = True

            return jsonify({"message": "All POIs cleared"})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Clear POIs error: {str(e)}")
        return jsonify({"error": str(e)}), 500


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


# ==================== 5. 更新POI优先级 ====================
@poi_bp.route('/api/user-pois/update-priority', methods=['POST'])
def update_poi_priority():
    """
    更新POI优先级（必去 ↔ 可选）

    Request Body:
        {
            "poi_id": "POI ID",
            "priority": "must_visit" | "optional"
        }

    Returns:
        {
            "message": "Priority updated",
            "poi_id": "...",
            "priority": "..."
        }
    """
    try:
        data = request.get_json()
        poi_id = data.get('poi_id', '').strip()
        new_priority = data.get('priority', '').strip()

        # 验证参数
        if not poi_id or new_priority not in ['must_visit', 'optional']:
            return jsonify({"error": "Invalid parameters"}), 400

        # 已登录用户：更新数据库
        if current_user.is_authenticated:
            favorite = UserPOIFavorite.query.filter_by(
                user_id=current_user.id,
                poi_id=poi_id
            ).first()

            if not favorite:
                return jsonify({"error": "POI not found"}), 404

            # 更新优先级
            favorite.priority = new_priority
            db.session.commit()

            logger.info(f"POI priority updated: user={current_user.username}, poi_id={poi_id}, priority={new_priority}")

            return jsonify({
                "message": "Priority updated",
                "poi_id": poi_id,
                "priority": new_priority
            })

        # 未登录用户：更新Session
        else:
            if 'user_selected_pois' not in session:
                return jsonify({"error": "No POIs in session"}), 404

            user_data = session['user_selected_pois']
            pois = user_data.get('pois', [])

            # 查找并更新POI
            updated = False
            for poi in pois:
                if poi.get('id') == poi_id:
                    poi['priority'] = new_priority
                    updated = True
                    break

            if not updated:
                return jsonify({"error": "POI not found"}), 404

            # 保存更新
            session['user_selected_pois'] = user_data
            session.modified = True

            logger.info(f"POI priority updated in session: poi_id={poi_id}, priority={new_priority}")

            return jsonify({
                "message": "Priority updated",
                "poi_id": poi_id,
                "priority": new_priority
            })

    except Exception as e:
        logger.error(f"Update POI priority error: {str(e)}")
        return jsonify({"error": str(e)}), 500


