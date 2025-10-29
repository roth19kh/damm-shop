from app import app, db, request
from flask import render_template, jsonify
from models.category import Category

import requests
from datetime import datetime
from flask_mail import Mail,Message

from werkzeug.utils import secure_filename
import os

@app.get("/admin/category")
def category_index():
    return render_template("admin/category/index.html" ,module='category')

@app.get("/admin/category/list")
def category_list():
    categories = get_category_list()
    return jsonify(categories)


@app.post("/admin/category/update")
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