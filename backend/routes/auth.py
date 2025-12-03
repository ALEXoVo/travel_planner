"""
用户认证路由
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required

from models import db
from models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册

    请求体：
    {
        "username": "testuser",
        "password": "password123",
        "email": "test@example.com"  // 可选
    }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()

        # 验证输入
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': '用户名长度应为3-50个字符'}), 400

        if len(password) < 6:
            return jsonify({'error': '密码长度至少6个字符'}), 400

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': '用户名已存在'}), 409

        # 创建新用户
        user = User(username=username, email=email if email else None)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        logger.info(f"User registered: {username}")

        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Register error: {str(e)}")
        return jsonify({'error': '注册失败，请稍后重试'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录

    请求体：
    {
        "username": "testuser",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400

        # 查找用户
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return jsonify({'error': '用户名或密码错误'}), 401

        # 登录用户
        login_user(user)

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()

        logger.info(f"User logged in: {username}")

        return jsonify({
            'message': '登录成功',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': '登录失败，请稍后重试'}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    return jsonify({'message': '登出成功'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前登录用户信息"""
    return jsonify({'user': current_user.to_dict()}), 200
