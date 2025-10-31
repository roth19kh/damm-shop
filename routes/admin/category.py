from app import app, db
from flask import render_template, jsonify, redirect, url_for, session, flash, request
from models.category import Category
from models.users import Users
from functools import wraps
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
        if not user or not getattr(user, 'is_admin', False):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


# Category Routes
@app.route("/admin/category")
@admin_required
def category_index():
    return render_template("admin/category/index.html", module='category')


@app.route("/admin/category/list")
@admin_required
def category_list():
    try:
        categories = get_category_list()
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/category/update", methods=['POST'])
@admin_required
def category_update():
    try:
        UPLOAD_DIR = os.path.join(app.root_path, "static", "image", "category")
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        category_id = request.form.get('id')
        category = Category.query.get(category_id)

        if not category:
            return jsonify({"error": "Category not found"}), 404

        # Update fields
        category.name = request.form.get('name')
        category.description = request.form.get('description')

        # Update image if new one is provided
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, filename)
            file.save(file_path)
            category.image = filename

        db.session.commit()
        return jsonify({"message": "Category updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/category/create", methods=['POST'])
@admin_required
def category_create():
    try:
        UPLOAD_DIR = os.path.join(app.root_path, "static", "image", "category")
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        file = request.files.get('image')
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, filename)
            file.save(file_path)

        new_category = Category(
            name=request.form.get('name'),
            image=filename,
            description=request.form.get('description'),
        )

        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category created successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/category/delete", methods=['POST'])
@admin_required
def category_delete():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        category_id = data.get('category_id')
        if not category_id:
            return jsonify({"error": "Category ID is required"}), 400

        category = Category.query.get(category_id)
        if category:
            db.session.delete(category)
            db.session.commit()
            return jsonify({"message": "Category deleted successfully"})
        return jsonify({"error": "Category not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_category_list():
    try:
        categories = Category.query.all()
        return [
            {
                "id": category.id,
                "name": category.name,
                "image": category.image,
                "description": category.description,
            }
            for category in categories
        ]
    except Exception as e:
        print(f"Error getting category list: {e}")
        return []


# Customer Routes
@app.route("/admin/customer")
@admin_required
def customer_index():
    return render_template("admin/customer/index.html", module='customer')


@app.route("/admin/customer/list")
@admin_required
def customer_list():
    try:
        customers = get_customer_list()
        return jsonify(customers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/customer/update", methods=['POST'])
@admin_required
def customer_update():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        customer_id = data.get('id')
        customer = Users.query.get(customer_id)

        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        # Update fields
        customer.name = data.get('name')
        customer.email = data.get('email')
        customer.gender = data.get('gender')
        customer.profile = data.get('profile')

        db.session.commit()
        return jsonify({"message": "Customer updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/customer/create", methods=['POST'])
@admin_required
def customer_create():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if email already exists
        existing_user = Users.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400

        customer = Users(
            name=data.get('name'),
            email=data.get('email'),
            gender=data.get('gender', 'male'),
            profile=data.get('profile', data.get('name')),
            password="default_password",  # You should hash this
            is_admin=False  # Default to non-admin
        )

        db.session.add(customer)
        db.session.commit()
        return jsonify({"message": "Customer created successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/admin/customer/delete", methods=['POST'])
@admin_required
def customer_delete():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        customer_id = data.get('customer_id')
        if not customer_id:
            return jsonify({"error": "Customer ID is required"}), 400

        customer = Users.query.get(customer_id)
        if customer:
            # Prevent deleting yourself
            if customer.id == session['user_id']:
                return jsonify({"error": "Cannot delete your own account"}), 400

            db.session.delete(customer)
            db.session.commit()
            return jsonify({"message": "Customer deleted successfully"})
        return jsonify({"error": "Customer not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_customer_list():
    try:
        customers = Users.query.all()
        return [
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "gender": customer.gender,
                "profile": customer.profile,
                "is_admin": getattr(customer, 'is_admin', False)
            }
            for customer in customers
        ]
    except Exception as e:
        print(f"Error getting customer list: {e}")
        return []