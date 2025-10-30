from app import app
from flask import render_template, redirect, url_for, session, flash
from models.users import Users
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


@app.route("/admin/customer")
@admin_required
def customer():
    return render_template("admin/customer/index.html", module='customer')