#!/usr/bin/python3
# -*- coding: utf-8 -*-
# made-on-the-knee-of (k) /dragon
  
import os, sys
import errno, traceback
import re, json
import tempfile
import time, signal
import datetime
import uuid
import logging

import psycopg2
import psycopg2.pool
import psycopg2.extras
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

# propagate using flask-login & flask-security instead of JWT
from flask import Flask, render_template, send_file, make_response, jsonify, request, redirect, url_for, g
from flask_login import LoginManager
from flask_http_middleware import MiddlewareManager, BaseHTTPMiddleware
from flask_principal import Principal, Permission, RoleNeed
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

__WD = os.path.abspath(os.path.dirname(__file__))

from .util import Pgpool, Cryptor 

db = SQLAlchemy()
pgpool = Pgpool()
cryptor = Cryptor()
login_manager = LoginManager()
loglevel = logging.DEBUG

from .models import User

@login_manager.user_loader
def user_load(id):
    return User.query.get(id)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login', next=request.path))

def create_app():
    app = Flask(__name__,static_url_path='/static',static_folder='static',template_folder='template')
    app.wsgi_app = ProxyFix( app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.config['cf'] = {
        'dbpool': {
            'minworkers': 2,
            'maxworkers': 4,
            'pg': {
                 'host':        os.environ.get('PG_HOST','localhost')
                ,'port':        int(os.environ.get('PG_PORT','5432'))
                ,'database':    os.environ.get('PG_DB','tinydap')
                ,'user':        os.environ.get('PG_USER','tinydap')
                ,'password':    os.environ.get('PG_PASSWORD','tinydap')
            }
        }
    }
    try:
        rsa = {}
        for k in ['private','public']:
            with open(os.path.join(__WD,'key','rsa.'+k)) as f:
                rsa[k] = f.read()
        app.config['RSA'] = rsa
    except:
        pass
    app.config.update({ 
        'SQLALCHEMY_DATABASE_URI': 'postgresql://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s'%(app.config['cf']['dbpool']['pg']),
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SECRET_KEY': os.getenv("SECRET_KEY", "1230416319513491576239881231582364592341301848123457623861285762921461837561296418236812351354134"),
        'BCRYPT_LOG_ROUNDS': 4
    })
    app.config['pipedir'] = "/tmp/tinydapipes"
    if not os.path.isdir(app.config['pipedir']):
        os.makedirs(app.config['pipedir'])

    db.init_app(app)
    pgpool.setapp(app)
    cryptor.setapp(app)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(loglevel)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
    login_manager.login_message = "Logon!"
    

    principals = Principal(app)
    

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .dap import dap as dap_blueprint
    app.register_blueprint(dap_blueprint)

    return app

application = create_app()

