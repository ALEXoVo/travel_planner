"""
数据库模型初始化模块
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .user import User
from .itinerary import Itinerary, ItineraryDay
from .poi import UserPOIFavorite
from .chat import ChatSession, ChatMessage
