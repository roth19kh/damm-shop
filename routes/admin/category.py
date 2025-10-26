from app import app, db, request
from flask import render_template
from models.category import Category

import requests
from datetime import datetime
from flask_mail import Mail,Message


@app.get("/admin/category")
def category_index():
    return render_template("admin/category/index.html" ,module='category')


@app.get("/admin/category/list")
def category_list():
    categories = get_category_list()
    return categories


@app.post("/admin/category/create")
def category_create():
    form = request.get_json()
    categories = Category(name=form.get('name'),
                          description=form.get('description'),
                          )
    db.session.add(categories)
    db.session.commit()
    return "Created category"


def get_category_list():
    return [
        {'id': 1, 'name': 'Electronics'},
        {'id': 2, 'name': 'Books'},
        {'id': 3, 'name': 'Clothing'},
        {'id': 4, 'name': 'Home & Kitchen'},
        {'id': 5, 'name': 'Sports & Outdoors'},
        {'id': 6, 'name': 'Toys & Games'},
        {'id': 7, 'name': 'Health & Personal Care'},
        {'id': 8, 'name': 'Automotive'},
        {'id': 9, 'name': 'Beauty'},
        {'id': 10, 'name': 'Grocery'},
    ]
