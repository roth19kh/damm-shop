from flask import Flask, render_template, jsonify, abort, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'haktharoth18@gmail.com'
app.config['MAIL_PASSWORD'] = 'bjbu yxgl hixz wriu'

mail = Mail(app)

# Your existing routes and models will work again


import models

import routes