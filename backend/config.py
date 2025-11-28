"""
配置管理模块

负责管理所有的环境变量、API密钥、CORS配置和应用常量。
"""
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """应用配置类"""

    # Flask配置
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8888

    # CORS配置
    CORS_RESOURCES = {
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }

    # 高德地图API配置
    AMAP_API_KEY = os.environ.get('AMAP_API_KEY', '195725c002640ec2e5a80b4775dd2189')

    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-d5826bdc14774b718b056a376bf894e0')

    # API超时配置（秒）
    AMAP_TIMEOUT = 15
    DEEPSEEK_TIMEOUT = 60

    # 默认坐标（北京天安门）
    DEFAULT_LNG = 116.397428
    DEFAULT_LAT = 39.90923

    # POI搜索配置
    POI_SEARCH_CONFIG = {
        'scenic': {
            'keywords': '',
            'types': '风景名胜',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        },
        'food': {
            'keywords': '美食',
            'types': '餐饮服务',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        },
        'hotel': {
            'keywords': '酒店',
            'types': '住宿服务',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        },
        'cultural': {
            'keywords': '博物馆|美术馆|文化中心|展览馆',
            'types': '科教文化服务',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        },
        'shopping': {
            'keywords': '购物中心|商场|百货',
            'types': '购物服务',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        },
        'parent_child': {
            'keywords': '亲子乐园|儿童乐园|动物园|水族馆|科技馆',
            'types': '休闲娱乐服务|科教文化服务|生活服务',
            'offset': 100,
            'page': 1,
            'extensions': 'all'
        }
    }

    # 交通方式选择阈值（米）
    TRANSPORT_THRESHOLD = {
        'walking': 1000,      # <1km 步行
        'transit': 10000,      # 1-5km 公交/地铁
        'driving': float('inf')  # >5km 驾车/打车
    }

    # 交通方式名称
    TRANSPORT_MODES = {
        'walking': '步行',
        'transit': '公交/地铁',
        'driving': '驾车/打车'
    }

    # AI生成配置
    AI_CONFIG = {
        'model': 'deepseek-chat',
        'temperature': 0.7,
        'tokens_per_day': 800,  # 每天行程预计消耗的token数
        'base_tokens': 500,     # 基础token消耗
        'max_tokens': 4000      # 最大token限制
    }

    # 路径优化配置（OR-Tools使用）
    ROUTE_OPTIMIZATION = {
        'max_time_per_day': 10 * 3600,  # 每天最多10小时（秒）
        'weather_weight': 0.3,           # 天气影响权重
        'traffic_weight': 0.4,           # 路况影响权重
        'distance_weight': 0.3,          # 距离影响权重
    }

    @classmethod
    def validate_api_keys(cls):
        """
        验证API密钥是否正确配置

        Returns:
            tuple: (amap_valid, deepseek_valid)
        """
        amap_valid = cls.AMAP_API_KEY and cls.AMAP_API_KEY != ''
        deepseek_valid = (
            cls.DEEPSEEK_API_KEY and
            cls.DEEPSEEK_API_KEY != '' and
            cls.DEEPSEEK_API_KEY != 'sk-d5826bdc14774b718b056a376bf894e0'
        )

        if not amap_valid:
            logger.warning("AMAP_API_KEY not set. Please set the AMAP_API_KEY environment variable.")

        if not deepseek_valid:
            logger.warning("DEEPSEEK_API_KEY not set or using default key. AI features will be disabled.")

        return amap_valid, deepseek_valid
