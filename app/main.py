# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from . import db, cryptor

main = Blueprint('main', __name__)


@main.route("/", endpoint="home", methods=["GET"])
@login_required
def home():
    return render_template("index.html", user=current_user)

