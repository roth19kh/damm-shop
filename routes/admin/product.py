from app import app, db, request
from flask import render_template, jsonify, redirect, url_for, session, flash
from models.category import Category
from models.users import Users
from models.product import Product
from functools import wraps


import requests
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os


# Admin protection
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))

        user = Users.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


# Product Routes
@app.get("/admin/product")
@admin_required
def product_index():
    return render_template("admin/product/index.html", module='product')


@app.get("/admin/product/list")
@admin_required
def product_list():
    products = get_product_list()
    return jsonify(products)


@app.post("/admin/product/update")
@admin_required
def product_update():
    UPLOAD_DIR = os.path.join("static/image", "product")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    form = request.form
    file = request.files.get('image')

    product_id = form.get('id')
    product = Product.query.get(product_id)

    if not product:
        return "Product not found", 404

    # Update fields - match your database schema
    product.name = form.get('title')
    product.price = float(form.get('price'))
    product.cost = float(form.get('price')) * 0.7
    product.category_id = form.get('category')
    product.stock = form.get('stock', 0)

    # Update image if new one is provided
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_DIR, filename))
        product.image = filename

    db.session.commit()
    return "Updated product"


@app.post("/admin/product/create")
@admin_required
def product_create():
    UPLOAD_DIR = os.path.join("static/image", "product")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    form = request.form
    file = request.files.get('image')

    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_DIR, filename))

    # Create product with your actual schema
    product = Product(
        name=form.get('title'),
        price=float(form.get('price')),
        cost=float(form.get('price')) * 0.7,
        category_id=form.get('category'),
        image=filename,
        stock=form.get('stock', 0)
    )
    db.session.add(product)
    db.session.commit()
    return "Created product"


@app.post("/admin/product/delete")
@admin_required
def product_delete():
    product_id = request.get_json().get('product_id')

    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return "Deleted product"
    return "Product not found", 404


def get_product_list():
    # 1. Get products from DATABASE
    database_products = [
        {
            "id": product.id,
            "title": product.name,
            "price": float(product.price),
            "cost": float(product.cost),
            "description": "",
            "category": product.category_id,
            "image": f"/static/image/product/{product.image}" if product.image else None,
            "stock": product.stock,
            "source": "database"  # Mark as from database
        }
        for product in Product.query.all()
    ]

    # 2. Get products from API
    api_products = [
        {
            "id": product['id'] + 1000,  # Add 1000 to avoid ID conflicts with database
            "title": product['title'],
            "price": product['price'],
            "cost": product['price'] * 0.7,  # Calculate cost
            "description": product['description'],
            "category": product['category'],
            "image": product['image'],
            "stock": 50,  # Default stock
            "source": "api"  # Mark as from API
        }
        for product in requests.get("https://fakestoreapi.com/products").json()
    ]

    # 3. COMBINE both lists
    all_products = database_products + api_products

    return all_products