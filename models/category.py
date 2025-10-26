from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    image = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(128), nullable=True)