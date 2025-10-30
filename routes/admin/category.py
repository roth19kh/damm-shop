from app import app, db, request
from flask import render_template, jsonify, redirect, url_for, session, flash
from models.category import Category
from models.users import Users  # Import your Users model
from functools import wraps

import requests
from datetime import datetime
from flask_mail import Mail, Message

from werkzeug.utils import secure_filename
import os


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please login to access admin panel.', 'warning')
            return redirect(url_for('login'))

        # Check if user is admin
        user = Users.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


# Category Routes
@app.get("/admin/category")
@admin_required
def category_index():
    return render_template("admin/category/index.html", module='category')


@app.get("/admin/category/list")
@admin_required
def category_list():
    categories = get_category_list()
    return jsonify(categories)


@app.post("/admin/category/update")
@admin_required
def category_update():
    UPLOAD_DIR = os.path.join("static/image", "category")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    form = request.form
    file = request.files.get('image')

    category_id = form.get('id')
    category = Category.query.get(category_id)

    if not category:
        return "Category not found", 404

    # Update fields
    category.name = form.get('name')
    category.description = form.get('description')

    # Update image if new one is provided
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_DIR, filename))
        category.image = filename

    db.session.commit()
    return "Updated category"


@app.post("/admin/category/create")
@admin_required
def category_create():
    UPLOAD_DIR = os.path.join("static/image", "category")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    form = request.form
    file = request.files.get('image')

    filename = None
    if file and file.filename:  # Check if file exists and has a filename
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_DIR, filename))

    categories = Category(name=form.get('name'),
                          image=filename,
                          description=form.get('description'),
                          )
    db.session.add(categories)
    db.session.commit()
    return "Created category"


@app.post("/admin/category/delete")
@admin_required
def category_delete():
    # Use get_json() since frontend sends JSON
    category_id = request.get_json().get('category_id')

    categories = Category.query.get(category_id)
    if categories:
        db.session.delete(categories)
        db.session.commit()
        return "Deleted category"
    return "Category not found", 404


def get_category_list():
    return [
        {
            "id": category.id,
            "name": category.name,
            "image": category.image,
            "description": category.description,
        }
        for category in Category.query.all()
    ]


# Customer Routes
@app.get("/admin/customer")
@admin_required
def customer_index():
    return render_template("admin/customer/index.html", module='customer')


@app.get("/admin/customer/list")
@admin_required
def customer_list():
    customers = get_customer_list()
    return jsonify(customers)


@app.post("/admin/customer/update")
@admin_required
def customer_update():
    data = request.get_json()

    customer_id = data.get('id')
    customer = Users.query.get(customer_id)

    if not customer:
        return "Customer not found", 404

    # Update fields
    customer.name = data.get('name')
    customer.email = data.get('email')
    customer.gender = data.get('gender')
    customer.profile = data.get('profile')

    db.session.commit()
    return "Updated customer"


@app.post("/admin/customer/create")
@admin_required
def customer_create():
    data = request.get_json()

    customer = Users(
        name=data.get('name'),
        email=data.get('email'),
        gender=data.get('gender'),
        profile=data.get('profile'),
        password="default_password"  # You might want to handle passwords differently
    )
    db.session.add(customer)
    db.session.commit()
    return "Created customer"


@app.post("/admin/customer/delete")
@admin_required
def customer_delete():
    customer_id = request.get_json().get('customer_id')

    customer = Users.query.get(customer_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        return "Deleted customer"
    return "Customer not found", 404


def get_customer_list():
    return [
        {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "gender": customer.gender,
            "profile": customer.profile,
        }
        for customer in Users.query.all()
    ]