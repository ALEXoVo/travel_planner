"""
POI收藏模型
"""
import json
from datetime import datetime
from . import db


class UserPOIFavorite(db.Model):
    __tablename__ = 'user_poi_favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination_city = db.Column(db.String(50), nullable=False)
    poi_name = db.Column(db.String(200), nullable=False)
    poi_id = db.Column(db.String(100))
    location = db.Column(db.Text)  # JSON: {lng, lat}
    poi_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'destination_city', 'poi_id', name='unique_user_poi'),
    )

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'poi_name': self.poi_name,
            'poi_id': self.poi_id,
            'location': json.loads(self.location) if self.location else None,
            'poi_type': self.poi_type,
            'created_at': self.created_at.isoformat()
        }
