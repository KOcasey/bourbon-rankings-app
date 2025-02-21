from flask_sqlalchemy import SQLAlchemy
from extensions import db


class Spirit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    distillery = db.Column(db.String(100), nullable=True)
    proof = db.Column(db.Float, nullable=True)
    age = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    spirit_type = db.Column(db.String(50), nullable=False)  # New column

    rankings = db.relationship('Ranking', backref='spirit', lazy=True, cascade="all, delete")
    reviews = db.relationship('Review', backref='spiirt', lazy=True, cascade="all, delete")


class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spirit_id = db.Column(
        db.Integer, 
        db.ForeignKey('spirit.id', name="fk_ranking_spirit"), nullable=False
    )  
    drink_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spirit_id = db.Column(
        db.Integer, 
        db.ForeignKey('spirit.id', name="fk_review_spirit"), nullable=False
    )  
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    drink_type = db.Column(db.String(50), nullable=False)