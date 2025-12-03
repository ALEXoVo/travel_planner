"""
行程模型
"""
import json
from datetime import datetime
from . import db


class Itinerary(db.Model):
    __tablename__ = 'itineraries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    destination_city = db.Column(db.String(50), nullable=False)
    origin_city = db.Column(db.String(50))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.String(50))
    travelers = db.Column(db.Integer)
    travel_styles = db.Column(db.Text)  # JSON数组
    summary = db.Column(db.Text)        # JSON对象
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    days = db.relationship('ItineraryDay', backref='itinerary', cascade='all, delete-orphan', order_by='ItineraryDay.day_number')

    def to_dict(self, include_days=True):
        """序列化为字典"""
        result = {
            'id': self.id,
            'title': self.title,
            'destination_city': self.destination_city,
            'origin_city': self.origin_city,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'budget': self.budget,
            'travelers': self.travelers,
            'travel_styles': json.loads(self.travel_styles) if self.travel_styles else [],
            'summary': json.loads(self.summary) if self.summary else {},
            'created_at': self.created_at.isoformat()
        }
        if include_days:
            result['days'] = [day.to_dict() for day in self.days]
        return result


class ItineraryDay(db.Model):
    __tablename__ = 'itinerary_days'

    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itineraries.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    activities = db.Column(db.Text, nullable=False)  # JSON数组

    def to_dict(self):
        """序列化为字典"""
        return {
            'day': self.day_number,
            'activities': json.loads(self.activities) if self.activities else []
        }
