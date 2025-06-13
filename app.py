from flask import Flask
from flask_login import LoginManager
from extensions import db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sonhos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import *
from views import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 