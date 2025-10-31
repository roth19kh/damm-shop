from flask import Flask, render_template, jsonify, abort, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://roth:x7Y7FALpSmfl5nS1iyMyf4zUA8lEq8FL@dpg-d41q71jipnbc73bsk85g-a.oregon-postgres.render.com/flask_lnt7'
app.config['SECRET_KEY'] = '5bae2b11e01ff0c318ed744434506229b46a298c7e7ef52a2f3bb171130c65cf'  # Make this more secure!
app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)


if __name__ == '__main__':
    app.run(debug=True)

    import models
    import routes