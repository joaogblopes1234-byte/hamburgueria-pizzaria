import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from models import db, User, Category, Product, Neighborhood, Order, OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testesecret'

@app.route('/')
@app.route('/<path:path>')
def hello(path=''):
    return "Vercel está VIVO! O problema era no Banco de Dados ou no Flask-Admin."

# TBD: Restore the rest of the application


if __name__ == '__main__':
    app.run(debug=True)
