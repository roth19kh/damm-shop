from app import app
from flask import render_template

import requests
from datetime import datetime
from flask_mail import Mail,Message


@app.route("/admin")
@app.route("/admin/dashboard")
def dashboard():
    return render_template("admin/dashboard/index.html", module='dashboard')
