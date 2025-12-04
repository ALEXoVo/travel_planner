"""
用户自定义活动模型

用于存储用户在行程中添加的自定义活动（非POI类型）
例如："21:00 在某处吃夜宵"、"休息"等
"""
import json
from datetime import datetime
from . import db


class UserActivity(db.Model):
    __tablename__ = 'user_activities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 可为空（支持未登录用户）
    session_id = db.Column(db.String(100), nullable=True)  # Session标识（未登录用户）
    itinerary_id = db.Column(db.String(50), nullable=False)  # 所属行程
    day_index = db.Column(db.Integer, nullable=False)  # 第几天（从0开始）
    activity_text = db.Column(db.String(500), nullable=False)  # 活动描述
    time_slot = db.Column(db.String(50), nullable=True)  # 时间段（如"21:00"）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'day_index': self.day_index,
            'activity_text': self.activity_text,
            'time_slot': self.time_slot,
            'created_at': self.created_at.isoformat()
        }
