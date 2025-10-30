from flask import Flask, render_template, jsonify, abort, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://roth:x7Y7FALpSmfl5nS1iyMyf4zUA8lEq8FL@dpg-d41q71jipnbc73bsk85g-a.oregon-postgres.render.com/flask_lnt7'
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)


import models
import routes

if __name__ == '__main__':
    app.run(debug=True)