"""
行程相关路由模块

处理行程生成和AI聊天助手的API端点。
"""
from flask import Blueprint, request, jsonify, session
from flask_login import current_user, login_required
from datetime import datetime
import logging
import json

from models import db
from models.itinerary import Itinerary, ItineraryDay
from services.itinerary_builder import ItineraryBuilder
from services.user_poi_itinerary_builder import UserPoiItineraryBuilder
from services.ai_service import AIService
from services.amap_service import AmapService
from utils.prompts import build_chat_system_prompt

logger = logging.getLogger(__name__)

# 创建Blueprint
itinerary_bp = Blueprint('itinerary', __name__)


@itinerary_bp.route('/api/itinerary/generate', methods=['POST'])
def generate_itinerary():
    """
    生成旅游行程计划（支持重新规划）。

    Request Body:
        {
            "destinationCity": "目的地城市",
            "originCity": "出发城市（可选）",
            "startDate": "开始日期 YYYY-MM-DD",
            "endDate": "结束日期 YYYY-MM-DD",
            "budget": "预算",
            "budgetType": "preset/custom",
            "customBudget": "自定义预算（可选）",
            "travelers": 出行人数,
            "travelStyles": ["旅游风格列表"],
            "replanMode": "incremental" | "complete" | null,  // 新增：重新规划模式
            "previousItinerary": {...},  // 新增：上次的行程数据
            "userPOIs": [...]  // 新增：用户添加的POI列表
        }

    Returns:
        JSON: 完整的行程数据，包含每天的活动、天气、交通等信息
    """
    try:
        # 解析请求数据
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # 提取重新规划相关参数
        replan_mode = data.get('replanMode', None)
        previous_itinerary = data.get('previousItinerary', None)
        user_pois = data.get('userPOIs', [])

        logger.info(f"Generating itinerary for {data.get('destinationCity')}, replan_mode={replan_mode}")

        # 创建行程构建器
        builder = ItineraryBuilder()

        # 构建行程（传递重新规划参数）
        itinerary = builder.build_itinerary(
            user_preferences=data,
            replan_mode=replan_mode,
            previous_itinerary=previous_itinerary,
            user_pois=user_pois
        )

        # 🆕 如果用户已登录，保存到数据库
        itinerary_id = None
        if current_user.is_authenticated:
            try:
                # 解析日期
                start_date_obj = datetime.strptime(data.get('startDate'), '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(data.get('endDate'), '%Y-%m-%d').date()

                # 生成标题
                destination_city = data.get('destinationCity')
                num_days = len(itinerary.get('itinerary', []))
                title = f"{destination_city}{num_days}日游"

                # 创建行程记录
                itinerary_record = Itinerary(
                    user_id=current_user.id,
                    title=title,
                    destination_city=destination_city,
                    origin_city=data.get('originCity'),
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    budget=data.get('budget'),
                    travelers=data.get('travelers'),
                    travel_styles=json.dumps(data.get('travelStyles', [])),
                    summary=json.dumps(itinerary.get('summary', {}))
                )
                db.session.add(itinerary_record)
                db.session.flush()  # 获取itinerary.id

                # 保存每天的活动
                for day_data in itinerary.get('itinerary', []):
                    day = ItineraryDay(
                        itinerary_id=itinerary_record.id,
                        day_number=day_data.get('day'),
                        activities=json.dumps(day_data.get('activities', []))
                    )
                    db.session.add(day)

                db.session.commit()
                itinerary_id = itinerary_record.id
                logger.info(f"Itinerary saved to DB: user={current_user.username}, id={itinerary_id}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to save itinerary to DB: {str(e)}")
                # 不影响行程返回，继续执行

        # 返回结果（新增itinerary_id字段）
        result = itinerary.copy()
        result['itinerary_id'] = itinerary_id
        return jsonify(result)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        return jsonify({
            "error": "无法生成行程计划，请稍后重试",
            "details": str(e)
        }), 500


@itinerary_bp.route('/api/assistant/chat', methods=['POST'])
def ai_assistant_chat():
    """
    AI助手对话接口。

    Request Body:
        {
            "message": "用户消息",
            "history": [对话历史],
            "destination_city": "目的地城市（可选）",
            "travel_date": "旅游日期（可选）"
        }

    Returns:
        JSON: {
            "response": "AI回复",
            "timestamp": "时间戳"
        }
    """
    try:
        data = request.get_json(force=True)
        message = data.get('message')
        conversation_history = data.get('history', [])
        destination_city = data.get('destination_city', '')
        travel_date = data.get('travel_date', '')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # 初始化服务
        ai_service = AIService()

        # 获取天气信息（如果有目的地和日期）
        weather_info = None
        if destination_city and travel_date:
            try:
                amap_service = AmapService()
                weather_data = amap_service.get_weather(destination_city)

                if weather_data and weather_data.get('forecasts'):
                    forecasts = weather_data['forecasts']
                    for forecast in forecasts:
                        if forecast.get('date') == travel_date or travel_date in forecast.get('date', ''):
                            weather_info = forecast
                            break

                    # 如果没找到特定日期，使用第一天
                    if not weather_info and forecasts:
                        weather_info = forecasts[0]

            except Exception as e:
                logger.error(f"Failed to get weather info: {str(e)}")

        # 构建系统提示词
        system_prompt = build_chat_system_prompt(weather_info)

        # 调用AI聊天
        ai_response = ai_service.chat(
            message=message,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        )

        return jsonify({
            "response": ai_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        logger.error(f"AI assistant error: {str(e)}")
        return jsonify({
            "response": "抱歉，AI助手当前不可用。请稍后再试。",
            "error": str(e)
        }), 500


@itinerary_bp.route('/api/itinerary/generate-from-user-pois', methods=['POST'])
def generate_itinerary_from_user_pois():
    """
    基于用户选择的POI生成行程。

    Request Body:
        {
            "start_date": "2024-10-01",
            "end_date": "2024-10-03",
            "destination_city": "北京",
            "user_pois_only": false,              # 是否仅规划用户POI（不添加餐厅/酒店）
            "optimization_strategy": "balanced",   # 'all' | 'shortest' | 'fastest' | 'balanced'
            "travelers": 2,
            "budget": "3000-5000"
        }

    Returns:
        JSON: {
            "itinerary": {
                "days": [...],
                "destination": "北京",
                "start_date": "2024-10-01",
                "end_date": "2024-10-03"
            },
            "summary": {
                "total_days": 3,
                "total_pois": 5,
                "user_pois_only": false,
                "selected_strategy": "balanced"
            },
            "route_strategies": {  # 仅当 optimization_strategy='all' 时返回
                "fastest": {...},
                "shortest": {...},
                "balanced": {...}
            }
        }
    """
    try:
        # 1. 从Session读取用户选择的POI
        user_data = session.get('user_selected_pois', {})
        user_pois = user_data.get('pois', [])

        if not user_pois:
            return jsonify({
                "error": "No POIs selected",
                "message": "请先选择至少一个POI。可使用 /api/poi/autocomplete 搜索并通过 /api/user-pois/add 添加POI。"
            }), 400

        # 2. 获取请求数据
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # 3. 验证必需字段
        required_fields = ['start_date', 'end_date', 'destination_city']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        destination_city = data['destination_city']

        # 4. 验证城市一致性
        session_city = user_data.get('destination_city', '')
        if session_city and session_city != destination_city:
            return jsonify({
                "error": "City mismatch",
                "message": f"Session中的POI属于 {session_city}，但请求的目的地是 {destination_city}。请清空POI列表后重新选择。"
            }), 400

        # 5. 构建偏好设置
        preferences = {
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'destination_city': destination_city,
            'user_pois_only': data.get('user_pois_only', False),
            'optimization_strategy': data.get('optimization_strategy', 'balanced'),
            'travelers': data.get('travelers', 2),
            'budget': data.get('budget', '3000-5000')
        }

        logger.info(f"Generating itinerary from {len(user_pois)} user POIs for {destination_city}")

        # 6. 调用UserPoiItineraryBuilder生成行程
        builder = UserPoiItineraryBuilder()
        itinerary_result = builder.build_itinerary_from_user_pois(
            user_pois=user_pois,
            preferences=preferences
        )

        return jsonify(itinerary_result)

    except ValueError as e:
        logger.error(f"Validation error in user POI itinerary: {str(e)}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error generating itinerary from user POIs: {str(e)}")
        return jsonify({
            "error": "无法生成行程计划，请稍后重试",
            "details": str(e)
        }), 500


# 🆕 ========== 行程历史管理 ========== #

@itinerary_bp.route('/api/itinerary/history', methods=['GET'])
@login_required
def get_itinerary_history():
    """
    获取用户行程历史列表

    查询参数：
    - page: 页码（默认1）
    - per_page: 每页数量（默认10）
    - destination_city: 过滤目的地（可选）
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        destination_city = request.args.get('destination_city', '').strip()

        # 构建查询
        query = Itinerary.query.filter_by(user_id=current_user.id)

        if destination_city:
            query = query.filter_by(destination_city=destination_city)

        # 分页查询
        pagination = query.order_by(Itinerary.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # 序列化结果（不包含详细活动，减少数据量）
        items = [itinerary.to_dict(include_days=False) for itinerary in pagination.items]

        return jsonify({
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        logger.error(f"Get itinerary history error: {str(e)}")
        return jsonify({'error': '获取历史行程失败'}), 500


@itinerary_bp.route('/api/itinerary/history/<int:itinerary_id>', methods=['GET'])
@login_required
def get_itinerary_detail(itinerary_id):
    """
    获取行程详情（包含完整活动数据）
    """
    try:
        itinerary = Itinerary.query.filter_by(
            id=itinerary_id,
            user_id=current_user.id  # 确保只能查看自己的行程
        ).first()

        if not itinerary:
            return jsonify({'error': '行程不存在或无权访问'}), 404

        return jsonify(itinerary.to_dict(include_days=True)), 200

    except Exception as e:
        logger.error(f"Get itinerary detail error: {str(e)}")
        return jsonify({'error': '获取行程详情失败'}), 500


@itinerary_bp.route('/api/itinerary/history/<int:itinerary_id>', methods=['DELETE'])
@login_required
def delete_itinerary(itinerary_id):
    """
    删除行程
    """
    try:
        itinerary = Itinerary.query.filter_by(
            id=itinerary_id,
            user_id=current_user.id
        ).first()

        if not itinerary:
            return jsonify({'error': '行程不存在或无权删除'}), 404

        db.session.delete(itinerary)
        db.session.commit()

        logger.info(f"Itinerary deleted: id={itinerary_id}, user={current_user.username}")

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete itinerary error: {str(e)}")
        return jsonify({'error': '删除失败'}), 500
