# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

from sqlalchemy import or_, ARRAY
from flask_login import UserMixin
import uuid
from . import db


class User(db.Model, UserMixin):
    
    __tablename__ = 'users'
    
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(128))
    fullname = db.Column(db.String(256))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(128))
    enable = db.Column(db.Boolean, default=True)
    password = db.Column(db.String(128))
    roles = db.Column(ARRAY(db.String), default=[])
    requiz = db.Column(db.JSON)
    meta = db.Column(db.JSON)
    
    @classmethod
    def find_by_ident(cls, ident):
        return cls.query.filter(or_( \
            cls.username == ident, 
            cls.email == ident, 
            cls.phone == ident \
            )).first()    



