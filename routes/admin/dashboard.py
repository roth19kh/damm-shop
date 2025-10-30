from app import app, db
from flask import render_template, redirect, url_for, session, flash
from models.users import Users
from models.category import Category
from models.product import Product
from models.order import Order
from functools import wraps

import requests
from datetime import datetime
from flask_mail import Mail, Message


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


@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def dashboard():
    try:
        print("🔄 Loading dashboard data...")

        # Get basic counts
        category_count = Category.query.count() or 0
        product_count = Product.query.count() or 0
        user_count = Users.query.filter_by(is_admin=True).count() or 0
        customer_count = Users.query.filter_by(is_admin=False).count() or 0
        order_count = Order.query.count() or 0
        pending_orders_count = Order.query.filter_by(status='pending').count() or 0

        # Calculate total revenue - multiple strategies
        print("💰 Calculating revenue...")

        # Strategy 1: Delivered orders only
        delivered_orders = Order.query.filter_by(status='delivered').all()
        delivered_revenue = sum(float(order.total_amount or 0) for order in delivered_orders)
        print(f"   Delivered orders revenue: ${delivered_revenue:.2f}")

        # Strategy 2: All completed statuses
        completed_statuses = ['delivered', 'completed', 'shipped', 'paid']
        completed_orders = Order.query.filter(Order.status.in_(completed_statuses)).all()
        completed_revenue = sum(float(order.total_amount or 0) for order in completed_orders)
        print(f"   All completed orders revenue: ${completed_revenue:.2f}")

        # Strategy 3: All orders (for testing)
        all_orders = Order.query.all()
        all_orders_revenue = sum(float(order.total_amount or 0) for order in all_orders)
        print(f"   All orders revenue: ${all_orders_revenue:.2f}")

        # Use the best available revenue
        if delivered_revenue > 0:
            final_revenue = delivered_revenue
            print("   Using delivered orders revenue")
        elif completed_revenue > 0:
            final_revenue = completed_revenue
            print("   Using all completed orders revenue")
        else:
            final_revenue = all_orders_revenue
            print("   Using all orders revenue")

        print(f"   Final revenue: ${final_revenue:.2f}")

        return render_template("admin/dashboard/index.html",
                             module='dashboard',
                             category_count=category_count,
                             product_count=product_count,
                             user_count=user_count,
                             customer_count=customer_count,
                             order_count=order_count,
                             pending_orders_count=pending_orders_count,
                             total_revenue=final_revenue)

    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()

        # Return safe default values
        return render_template("admin/dashboard/index.html",
                             module='dashboard',
                             category_count=0,
                             product_count=0,
                             user_count=0,
                             customer_count=0,
                             order_count=0,
                             pending_orders_count=0,
                             total_revenue=0)