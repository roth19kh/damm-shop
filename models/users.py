from app import db

class Users(db.Model):
    __tablename__ = 'customer'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    password = db.Column(db.String(128))
    gender = db.Column(db.String(128), default='male')
    profile = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)  # Add this field