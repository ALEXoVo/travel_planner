"""
Travel Planner Backend Application

智能旅游行程规划助手后端服务。
整合高德地图API、DeepSeek AI、OR-Tools路径优化等功能。
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_session import Session  # 新增：导入Flask-Session
import logging
import os
from datetime import timedelta

from config import Config
from models import db
from routes.itinerary import itinerary_bp
from routes.map import map_bp
from routes.poi import poi_bp
from routes.auth import auth_bp
from routes.activity import activity_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    创建并配置Flask应用。

    Returns:
        Flask: 配置好的Flask应用实例
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(Config)

    # 🆕 Session配置 - 用于用户POI选择临时存储
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
    app.config['SESSION_FILE_THRESHOLD'] = 500

    # Cookie配置 - 支持跨域和本地文件访问
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # 允许跨站点Cookie
    app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境HTTP（生产应设为True）
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问Cookie
    app.config['SESSION_COOKIE_NAME'] = 'travelplanner_session'

    # 🆕 数据库配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travelplanner.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 配置CORS - 支持携带Cookie
    CORS(app, resources=Config.CORS_RESOURCES, supports_credentials=True)

    # 🆕 初始化Flask-Session（必须在配置之后）
    Session(app)
    logger.info("Flask-Session initialized with filesystem storage")

    # 🆕 初始化数据库
    db.init_app(app)

    # 🆕 初始化Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # 注册路由蓝图
    register_blueprints(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 🆕 创建数据库表
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

    # 验证API密钥
    Config.validate_api_keys()

    # 根路由
    @app.route('/')
    def home():
        """API欢迎页面"""
        return jsonify({
            "message": "Travel Planner Backend API",
            "version": "2.0",
            "status": "running",
            "endpoints": {
                "auth": {
                    "register": "POST /api/auth/register",
                    "login": "POST /api/auth/login",
                    "logout": "POST /api/auth/logout",
                    "me": "GET /api/auth/me"
                },
                "itinerary": {
                    "generate": "POST /api/itinerary/generate",
                    "generate_from_user_pois": "POST /api/itinerary/generate-from-user-pois",
                    "chat": "POST /api/assistant/chat",
                    "history": "GET /api/itinerary/history",
                    "detail": "GET /api/itinerary/history/<id>",
                    "delete": "DELETE /api/itinerary/history/<id>"
                },
                "map": {
                    "route_planning": "POST /api/route/planning",
                    "weather": "GET /api/weather/info"
                },
                "poi": {
                    "autocomplete": "GET /api/poi/autocomplete",
                    "add": "POST /api/user-pois/add",
                    "list": "GET /api/user-pois/list",
                    "remove": "DELETE /api/user-pois/remove/<poi_id>",
                    "clear": "DELETE /api/user-pois/clear",
                    "optimize": "POST /api/poi/optimize"
                }
            }
        })

    logger.info("Flask application created successfully")
    return app


def register_blueprints(app: Flask):
    """
    注册所有路由蓝图。

    Args:
        app: Flask应用实例
    """
    app.register_blueprint(itinerary_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(poi_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_bp)

    logger.info("Blueprints registered: itinerary, map, poi, auth, activity")


def register_error_handlers(app: Flask):
    """
    注册全局错误处理器。

    Args:
        app: Flask应用实例
    """

    @app.errorhandler(404)
    def not_found(error):
        """处理404错误"""
        logger.error(f"Endpoint not found: {error}")
        return jsonify({
            "error": "Endpoint not found",
            "message": "请求的API端点不存在"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """处理405错误"""
        logger.error(f"Method not allowed: {error}")
        return jsonify({
            "error": "Method not allowed for the requested URL",
            "message": "请求方法不允许"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "error": "Internal server error",
            "message": "服务器内部错误"
        }), 500

    logger.info("Error handlers registered")


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    logger.info(f"Starting Travel Planner Backend on {Config.HOST}:{Config.PORT}")
    logger.info(f"Debug mode: {Config.DEBUG}")

    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
