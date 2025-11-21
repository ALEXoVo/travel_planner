"""
行程相关路由模块

处理行程生成和AI聊天助手的API端点。
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from services.itinerary_builder import ItineraryBuilder
from services.ai_service import AIService
from services.amap_service import AmapService
from utils.prompts import build_chat_system_prompt

logger = logging.getLogger(__name__)

# 创建Blueprint
itinerary_bp = Blueprint('itinerary', __name__)


@itinerary_bp.route('/api/itinerary/generate', methods=['POST'])
def generate_itinerary():
    """
    生成旅游行程计划。

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
            "travelStyles": ["旅游风格列表"]
        }

    Returns:
        JSON: 完整的行程数据，包含每天的活动、天气、交通等信息
    """
    try:
        # 解析请求数据
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        logger.info(f"Generating itinerary for {data.get('destinationCity')}")

        # 创建行程构建器
        builder = ItineraryBuilder()

        # 构建行程
        itinerary = builder.build_itinerary(data)

        return jsonify(itinerary)

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
