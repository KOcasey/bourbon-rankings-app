from flask_sqlalchemy import SQLAlchemy
from extensions import db


class Bourbon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    rankings = db.relationship('Ranking', backref='bourbon', lazy=True)

class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bourbon_id = db.Column(db.Integer, db.ForeignKey('bourbon.id'), nullable=False)
    drink_type = db.Column(db.String(50), nullable=False)  # e.g., Neat, On the Rocks
    score = db.Column(db.Float, nullable=False)  # Ranking score (1-10)
    
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bourbon_id = db.Column(db.Integer, db.ForeignKey('bourbon.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)  # 1-10 scale
    drink_type = db.Column(db.String(50), nullable=False)  # Neat, on the rocks, etc.