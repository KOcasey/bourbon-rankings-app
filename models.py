from flask_sqlalchemy import SQLAlchemy
from extensions import db


class Bourbon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    rankings = db.relationship('Ranking', backref='bourbon', lazy=True)
    reviews = db.relationship('Review', backref='bourbon', lazy=True)  # Added for completeness

class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bourbon_id = db.Column(db.Integer, db.ForeignKey('bourbon.id'), nullable=False)  # Corrected foreign key
    drink_type = db.Column(db.String(50), nullable=False)  # Type of drink (Neat, On the Rocks, etc.)
    score = db.Column(db.Float, nullable=False)  # Rating score
    description = db.Column(db.Text, nullable=True)  # Optional description

    def __repr__(self):
        return f'<Ranking {self.bourbon.name} - {self.drink_type}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bourbon_id = db.Column(db.Integer, db.ForeignKey('bourbon.id'), nullable=False)  # Foreign key reference
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)  # 1-10 scale
    drink_type = db.Column(db.String(50), nullable=False)  # Neat, on the rocks, etc.