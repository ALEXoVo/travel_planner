"""
用户活动管理路由

处理用户自定义活动的添加、查询和删除
活动与POI的区别：活动是用户自定义的文本描述（如"21:00 吃夜宵"），不触发重新规划
"""
from flask import Blueprint, request, jsonify, session
from flask_login import current_user
import logging

from models import db
from models.activity import UserActivity

logger = logging.getLogger(__name__)

# 创建Blueprint
activity_bp = Blueprint('activity', __name__)


# ==================== 1. 添加自定义活动 ====================
@activity_bp.route('/api/activities/add', methods=['POST'])
def add_activity():
    """
    添加自定义活动到行程某一天

    Request Body:
        {
            "itinerary_id": "行程ID",
            "day_index": 0,  // 第几天（从0开始）
            "activity_text": "21:00 在某处吃夜宵",
            "time_slot": "21:00"  // 可选
        }

    Returns:
        {
            "message": "Activity added",
            "activity": {...}
        }
    """
    try:
        data = request.get_json()
        itinerary_id = data.get('itinerary_id', '').strip()
        day_index = data.get('day_index', 0)
        activity_text = data.get('activity_text', '').strip()
        time_slot = data.get('time_slot', '').strip()

        # 验证必填字段
        if not itinerary_id or not activity_text:
            return jsonify({"error": "itinerary_id and activity_text are required"}), 400

        # 已登录用户：保存到数据库
        if current_user.is_authenticated:
            activity = UserActivity(
                user_id=current_user.id,
                itinerary_id=itinerary_id,
                day_index=day_index,
                activity_text=activity_text,
                time_slot=time_slot
            )
            db.session.add(activity)
            db.session.commit()

            logger.info(f"Activity added to DB: user={current_user.username}, itinerary={itinerary_id}, day={day_index}")

            return jsonify({
                "message": "Activity added",
                "activity": activity.to_dict()
            })

        # 未登录用户：保存到Session
        else:
            if 'user_activities' not in session:
                session['user_activities'] = {}

            session_activities = session['user_activities']

            # 初始化该行程的活动列表
            if itinerary_id not in session_activities:
                session_activities[itinerary_id] = []

            # 创建活动数据
            activity_data = {
                'id': f"session_{len(session_activities[itinerary_id])}",
                'day_index': day_index,
                'activity_text': activity_text,
                'time_slot': time_slot
            }

            session_activities[itinerary_id].append(activity_data)
            session['user_activities'] = session_activities
            session.modified = True

            logger.info(f"Activity added to session: itinerary={itinerary_id}, day={day_index}")

            return jsonify({
                "message": "Activity added",
                "activity": activity_data
            })

    except Exception as e:
        logger.error(f"Add activity error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 2. 获取行程的活动列表 ====================
@activity_bp.route('/api/activities/list', methods=['GET'])
def list_activities():
    """
    获取指定行程的所有活动

    Query参数:
        itinerary_id: 行程ID（必需）

    Returns:
        {
            "activities": [...]
        }
    """
    try:
        itinerary_id = request.args.get('itinerary_id', '').strip()

        if not itinerary_id:
            return jsonify({"error": "itinerary_id is required"}), 400

        # 已登录用户：从数据库查询
        if current_user.is_authenticated:
            activities = UserActivity.query.filter_by(
                user_id=current_user.id,
                itinerary_id=itinerary_id
            ).order_by(UserActivity.day_index, UserActivity.created_at).all()

            return jsonify({
                "activities": [a.to_dict() for a in activities],
                "count": len(activities)
            })

        # 未登录用户：从Session读取
        else:
            session_activities = session.get('user_activities', {})
            activities = session_activities.get(itinerary_id, [])

            return jsonify({
                "activities": activities,
                "count": len(activities)
            })

    except Exception as e:
        logger.error(f"List activities error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== 3. 删除活动 ====================
@activity_bp.route('/api/activities/remove/<activity_id>', methods=['DELETE'])
def remove_activity(activity_id):
    """
    删除指定活动

    URL参数:
        activity_id: 活动ID

    Query参数:
        itinerary_id: 行程ID（Session用户必需）

    Returns:
        {
            "message": "Activity removed",
            "remaining_count": 5
        }
    """
    try:
        # 已登录用户：从数据库删除
        if current_user.is_authenticated:
            activity = UserActivity.query.filter_by(
                id=activity_id,
                user_id=current_user.id
            ).first()

            if not activity:
                return jsonify({"error": "Activity not found"}), 404

            itinerary_id = activity.itinerary_id
            db.session.delete(activity)
            db.session.commit()

            # 查询剩余数量
            remaining_count = UserActivity.query.filter_by(
                user_id=current_user.id,
                itinerary_id=itinerary_id
            ).count()

            logger.info(f"Activity removed from DB: user={current_user.username}, activity_id={activity_id}")

            return jsonify({
                "message": "Activity removed",
                "remaining_count": remaining_count
            })

        # 未登录用户：从Session删除
        else:
            itinerary_id = request.args.get('itinerary_id', '').strip()

            if not itinerary_id:
                return jsonify({"error": "itinerary_id is required for session users"}), 400

            if 'user_activities' not in session:
                return jsonify({"error": "No activities in session"}), 404

            session_activities = session['user_activities']
            activities_list = session_activities.get(itinerary_id, [])

            # 过滤掉指定活动
            original_count = len(activities_list)
            activities_list = [a for a in activities_list if a.get('id') != activity_id]

            if len(activities_list) == original_count:
                return jsonify({"error": "Activity not found"}), 404

            session_activities[itinerary_id] = activities_list
            session['user_activities'] = session_activities
            session.modified = True

            logger.info(f"Activity removed from session: activity_id={activity_id}")

            return jsonify({
                "message": "Activity removed",
                "remaining_count": len(activities_list)
            })

    except Exception as e:
        logger.error(f"Remove activity error: {str(e)}")
        return jsonify({"error": str(e)}), 500
