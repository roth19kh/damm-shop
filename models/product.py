from app import db

class Product(db.Model):
    __tablename__ = 'product'   # ✅ clear table name
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    cost = db.Column(db.Numeric(10, 2))
    price = db.Column(db.Numeric(10, 2))
    category_id = db.Column(db.Integer)
    image = db.Column(db.String(128), nullable=True)
    stock = db.Column(db.Integer, default=0)

