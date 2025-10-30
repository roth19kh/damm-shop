from app import app, db, request
from flask import render_template, jsonify, redirect, url_for, session, flash
from models.order import Order, OrderItem
from models.users import Users
from functools import wraps


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


@app.route("/admin/order")
@admin_required
def order_index():
    return render_template("admin/order_management/order_management.html", module='order')


@app.get("/admin/order/list")
@admin_required
def order_list():
    status_filter = request.args.get('status', '')
    orders = get_order_list(status_filter)
    return jsonify(orders)


@app.post("/admin/order/update-status")
@admin_required
def update_order_status():
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.status = new_status
    db.session.commit()

    return jsonify({"message": "Order status updated successfully"})


@app.get("/admin/order/details")
@admin_required
def order_details():
    order_id = request.args.get('order_id')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order_data = {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "city": order.city,
        "country": order.country,
        "payment_method": order.payment_method,
        "shipping_fee": float(order.shipping_fee),
        "total_amount": float(order.total_amount),
        "status": order.status,
        "order_date": order.order_date.strftime("%Y-%m-%d %H:%M"),
        "items": [
            {
                "product_name": item.product_name,
                "product_price": float(item.product_price),
                "quantity": item.quantity,
                "subtotal": float(item.subtotal)
            }
            for item in order.items
        ]
    }

    return jsonify(order_data)


def get_order_list(status_filter=''):
    query = Order.query

    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.order_date.desc()).all()

    return [
        {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M"),
            "item_count": len(order.items)
        }
        for order in orders
    ]