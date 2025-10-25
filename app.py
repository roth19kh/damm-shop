from flask import Flask, render_template,jsonify,abort,request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'


db = SQLAlchemy(app)
migrate = Migrate(app, db)

import models

import routes