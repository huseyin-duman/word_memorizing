from flask_login import UserMixin
from __init__ import db

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100))
    user_name = db.Column(db.String(1000))

class Dictionary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100))
    definition = db.Column(db.String(1000))

class UserWords(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100))
    user_name = db.Column(db.String(1000))
    search_count = db.Column(db.Integer)
    appearance_count = db.Column(db.Integer)
    practice_point = db.Column(db.Integer)
    power = db.Column(db.Integer)