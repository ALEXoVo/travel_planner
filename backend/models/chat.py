"""
聊天历史模型
"""
from datetime import datetime
from . import db


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime)

    # 关系
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan', order_by='ChatMessage.timestamp')

    def to_dict(self, include_messages=False):
        """序列化为字典"""
        result = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None
        }
        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]
        return result


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "user" | "assistant"
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """序列化为字典"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
