from app import app, db, request
from flask import render_template, jsonify, session, redirect, flash, abort
from models.users import Users
from werkzeug.security import generate_password_hash
from functools import wraps


# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access admin panel.', 'warning')
            return redirect('/login')

        user = Users.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect('/')

        return f(*args, **kwargs)

    return decorated_function


# Admin Users Routes
@app.get("/admin/user")
@admin_required
def user_index():
    return render_template("admin/users/index.html", module='user')


@app.get("/admin/user/list")
@admin_required
def user_list():
    users = get_user_list()
    return jsonify(users)


@app.post("/admin/user/update")
@admin_required
def user_update():
    data = request.get_json()

    user_id = data.get('id')
    user = Users.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update fields
    user.name = data.get('name')
    user.email = data.get('email')
    user.gender = data.get('gender')
    user.is_admin = data.get('is_admin', False)

    # Update password if provided
    if data.get('password'):
        user.password = generate_password_hash(data.get('password'))

    db.session.commit()
    return "Updated user"


@app.post("/admin/user/create")
@admin_required
def user_create():
    data = request.get_json()

    # Check if email already exists
    existing_user = Users.query.filter_by(email=data.get('email')).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    user = Users(
        name=data.get('name'),
        email=data.get('email'),
        password=generate_password_hash(data.get('password')),
        gender=data.get('gender', 'male'),
        is_admin=data.get('is_admin', False)
    )

    db.session.add(user)
    db.session.commit()
    return "Created user"


@app.post("/admin/user/delete")
@admin_required
def user_delete():
    user_id = request.get_json().get('user_id')

    # Prevent deleting yourself
    if user_id == session.get('user_id'):
        return jsonify({"error": "Cannot delete your own account"}), 400

    user = Users.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return "Deleted user"
    return jsonify({"error": "User not found"}), 404


def get_user_list():
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "gender": user.gender,
            "is_admin": user.is_admin,
            "profile": user.profile
        }
        for user in Users.query.all()
    ]