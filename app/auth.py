# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

import base64, json, sys
import logging
from random import randint
from sqlalchemy import text as sqltext
from flask import Blueprint, current_app, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, ValidationError
from wtforms.fields import BooleanField, StringField, PasswordField, HiddenField
from wtforms.fields import EmailField  

from . import db, cryptor, loglevel 
from .models import User

auth = Blueprint('auth', __name__)


def PhoneValidator():
    msg = "Must be a valid E.164 phone number"
    def _PhoneValidator(form, field):
        l = field.data and len(field.data) or 0
        if not ( l > 6 and field.data.startswith("+") and field.data[1:].isnumeric() ):
            raise ValidationError(msg + " : " + field.data)
    return _PhoneValidator            

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash("Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')



class ThisForm(FlaskForm):
    tag1        = HiddenField()
    tag2        = HiddenField()
    def fields(self):
        return {x:y.data for x,y in self._fields.items()}
    def prepare(self):
        self.tag1.data = cryptor.publickey()\
            .decode()\
            .replace("-----BEGIN PUBLIC KEY-----","")\
            .replace("-----END PUBLIC KEY-----","")

class LoginForm(ThisForm):
    ident       = StringField('ident', validators=[DataRequired()])
    password    = PasswordField('password', validators=[DataRequired()])
    rememberme  = BooleanField()

class RestoreForm(ThisForm):
    ident       = StringField('ident', validators=[DataRequired()])
    x           = HiddenField()
    q           = StringField()
    a           = StringField()
    i           = StringField()

class ChpassForm(ThisForm):
    target      = "";
    x           = HiddenField()
    tag3        = HiddenField()
    password    = PasswordField('password')
    password1   = PasswordField('password1')
    password2   = PasswordField('password2')

class RegisterForm(ThisForm):
    username    = StringField('username', validators=[DataRequired()])
    password1   = PasswordField('password1', validators=[DataRequired()])
    password2   = PasswordField('password2', validators=[DataRequired()])
    fullname    = StringField('fullname')
    email       = EmailField('email', validators=[DataRequired(), Email()])
    phone       = StringField('phone', validators=[DataRequired(), PhoneValidator()])
    quiz1       = StringField('quiz1')
    ans1        = StringField('ans1')
    quiz2       = StringField('quiz2')
    ans2        = StringField('ans2')
    quiz3       = StringField('quiz3')
    ans3        = StringField('ans3')

class ProfileForm(ThisForm):
    username    = StringField('username')
    fullname    = StringField('fullname')
    email       = EmailField('email', validators=[DataRequired(), Email()])
    phone       = StringField('phone', validators=[DataRequired(), PhoneValidator()])
    quiz1       = StringField('quiz1')
    ans1        = StringField('ans1')
    quiz2       = StringField('quiz2')
    ans2        = StringField('ans2')
    quiz3       = StringField('quiz3')
    ans3        = StringField('ans3')



@auth.route('/api/v1/check', endpoint="check", methods=["POST"])
def check():
    # TODO: extend
    data = request.stream.read()
    if data is not None and len(data) >  8:
        try:
            buf = cryptor.decrypt(base64.b64decode(data)).decode()
            obj = json.loads(buf)
            _do = obj.get('do')
            _what = obj.get('what')
            _val = obj.get('value')
            if _do == 'exists':
                if _what in ['username', 'email', 'phone']:
                    u = User.query.filter(sqltext("%s = '%s'" % (_what, _val))).first()    
                    return jsonify({ 'exists': (u is not None) })
                else:
                    return "Invalid object", 400
            else:
                return "Invalid object", 400
        except Exception as e:
            current_app.logger.error(e)
            return "Handler error", 500
    else:
        return "Bad data", 400



@auth.route("/login", endpoint="login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    form.prepare()
    if request.method == "POST": 
        if form.validate_on_submit():
            tag = form.tag2.data
            uid = None
            pwd = None
            if tag is None:
                uid = form.ident.data
                pwd = form.password.data
            else:
                buf = cryptor.decrypt(base64.b64decode(tag)).decode()
                if ":" in buf:
                    uid, pwd = buf.split(":", 1)
                else:
                    flash("Invalid username/password data", "error")
            if uid is not None:
                form.ident.data = uid
                user = User.find_by_ident(uid)
                if user is None or not check_password_hash(user.password, pwd):
                    flash("Invalid username/password", "error")
                else:
                    login_user(user)
                    current_app.logger.debug("User login successful | %s" % user.username)
                    return redirect(url_for("main.home"))
        else:
            current_app.logger.debug("User login failed")
    flash_errors(form)
    return render_template('auth/login.html', login_user_form=form, segment='login')

@auth.route('/register', endpoint="register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    form.prepare()
    if request.method == "POST": 
        tag = form.tag2.data
        if tag is not None and len(tag) > 0:
            try:
                buf = cryptor.decrypt(base64.b64decode(tag)).decode()
                sys.stdout.flush()
                obj = json.loads(buf)
                for k,v in obj.items():
                    _x = getattr(form,k)
                    sys.stdout.flush()
                    if v != _x.data:
                        _x.data = v
                        setattr(form,k,_x)
                if form.validate_on_submit():
                    obj['requiz'] = {'q': [obj['quiz1'],obj['quiz2'],obj['quiz3']], 'a': [obj['ans1'],obj['ans2'],obj['ans3']]}
                    del obj['quiz1']
                    del obj['quiz2']
                    del obj['quiz3']
                    del obj['ans1']
                    del obj['ans2']
                    del obj['ans3']
                    obj['password'] = generate_password_hash(obj['password1'])
                    del obj['password1']
                    del obj['password2']
                    u = User(**obj)
                    db.session.add(u)
                    db.session.commit()
                    return redirect(url_for('auth.login'))
                else:
                    flash("Invalid form data")
            except Exception as e:
                flash("Error hande processing")
                current_app.logger.error(e)
        else:
            flash("Invalid data")
    flash_errors(form)
    return render_template('auth/register.html', register_user_form=form, segment='login')

@auth.route('/logout', endpoint='logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/chpass', endpoint='chpass', methods=['GET', 'POST'])
@login_required
def chpass():
    form = ChpassForm()
    form.prepare()
    form.target = 'chpass'
    if request.method == "POST": 
        if form.validate_on_submit():
            tag  = form.tag2.data
            tag3 = form.tag3.data
            if tag is not None and len(tag) > 0:
                try:
                    uid = cryptor.decrypt(base64.b64decode(tag3)).decode()
                    if uid == current_user.username:
                        stag = cryptor.decrypt(base64.b64decode(tag)).decode()
                        p,p1,p2 = stag.split(":::")
                        current_app.logger.debug([p,p1,p2])
                        if check_password_hash(current_user.password,p):
                            if p1 == p2:
                                current_user.password = generate_password_hash(p1)
                                db.session.commit()
                                logout_user()
                                return redirect(url_for('auth.login'))
                            else:
                                flash("Passwords not match")
                        else:
                            flash("Invalid user password")
                            logout_user()
                            return redirect(url_for('auth.login'))
                    else:
                        flash("Wrong token")
                except Exception as e:
                    current_app.logger.error(e)
                    flash("Invalid token")
    else:
        form.tag3.data = base64.b64encode(cryptor.encrypt(current_user.username)).decode()
    flash_errors(form)
    return render_template('auth/chpass.html', chpass_user_form=form, segment='login')

@auth.route('/restore', endpoint="restore", methods=['GET', 'POST'])
def restore():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RestoreForm()
    form.prepare()    
    if request.method == "POST":
        tag = form.tag2.data
        if tag is not None and len(tag) > 0:
            stag = cryptor.decrypt(base64.b64decode(tag)).decode()
            if form.x.data == "requiz":
                uid = stag
                form.ident.data = uid
                current_app.logger.debug("Get requiz")
                user = User.find_by_ident(uid);
                if user is not None and 'q' in user.requiz:
                    q = []
                    j = []
                    for i,v in enumerate(user.requiz['q']):
                        if v is not None and len(v) > 0 and user.requiz['a'][i] is not None and len(user.requiz['a'][i]) > 0:
                            q.append(v)
                            j.append(i)
                    if len(q) > 0:
                        k = randint(0,len(q)-1)
                        return jsonify({'i': j[k], 'q': q[k]})
                    else:
                        flash("No required user data", error)
                else:
                    flash("Invalid user","error");                   
            elif form.x.data == "restore":
                current_app.logger.debug("Do restore")
                try:
                    uid, qid, ans = stag.split(":::")
                    qid = int(qid)
                    user = User.find_by_ident(uid);
                    if user is not None and 'q' in user.requiz:
                        qq = user.requiz['q'][qid]
                        aa = user.requiz['a'][qid]
                        form.ident.data = uid
                        form.i.data = qid
                        form.q.data = qq
                        form.a.data = None
                        if aa.strip().upper() == ans.strip().upper():
                            cform = ChpassForm()
                            cform.prepare()
                            cform.target = 'restore'
                            cform.tag3.data = base64.b64encode(cryptor.encrypt(uid+":::"+str(qid)+":::"+qq)).decode()
                            return render_template('auth/chpass.html', chpass_user_form=cform, segment='login')
                        else:
                            flash("Wrong answer")
                except Exception as e:
                    current_app.logger.error(e)
                    flash("Invalid restore form data")
            elif form.x.data == "chpass":
                tag3 = form.tag3.data
                if tag3 is not None and len(tag3) > 0:
                    try:
                        utag = cryptor.decrypt(base64.b64decode(tag3)).decode()
                        uid,qid,q = utag.split(":::")
                        user = User.find_by_ident(uid);
                        if user.requiz['q'][qid].strip().upper() == q.strip().upper():
                            p,p1,p2 = stag.split(":::")
                            if p1 == p2:
                                user.password = generate_password_hash(p1)
                                db.session.commit()
                                logout_user()
                                return redirect(url_for('main.home'))
                            else:
                                flash("Wrong token")
                        else:
                            flash("Wrong token")
                    except:
                        flash("Invalid token")
        else:
            flash("Invalid data", 'error');
    flash_errors(form)
    return render_template('auth/restore.html', restore_user_form=form, segment='login')

@auth.route('/profile', endpoint="profile", methods=["GET","POST"])
@login_required
def profile():
    form = ProfileForm()
    form.prepare()
    if request.method == "POST": 
        tag = form.tag2.data
        if tag is not None and len(tag) > 0:
            try:
                stag = cryptor.decrypt(base64.b64decode(tag)).decode()
                obj = json.loads(stag)
                if 'ident' in obj and obj['ident'] == current_user.username:
                    n = 0
                    for k in ['fullname','email','phone']:
                        if obj[k] != getattr(current_user, k):                        
                            setattr(current_user,k,obj[k])
                            n += 1
                    q = {"q": [obj['quiz%s' % j] for j in [1,2,3]], "a": [obj['ans%s' % j] for j in [1,2,3]]}
                    if current_user.requiz != q:
                        current_user.requiz = q
                        n += 1
                    if n > 0:
                        db.session.commit()                    
                    return redirect(url_for('main.home'))                    
                else:
                    flash("Invalid form data")
            except Exception as e:
                current_app.logger.error(e)
                flash("Invalid token")
        else:
            flash("Invalid data", 'error');
    form.username.data    =   current_user.username
    form.fullname.data    =   current_user.fullname 
    form.email.data       =   current_user.email   
    form.phone.data       =   current_user.phone   
    form.quiz1.data       =   current_user.requiz['q'][0]   
    form.ans1.data        =   current_user.requiz['a'][0]   
    form.quiz2.data       =   current_user.requiz['q'][1]  
    form.ans2.data        =   current_user.requiz['a'][1]  
    form.quiz3.data       =   current_user.requiz['q'][2] 
    form.ans3.data        =   current_user.requiz['a'][2] 
    flash_errors(form)
    return render_template('auth/profile.html', profile_user_form=form, segment='login')

