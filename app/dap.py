# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

import base64, json, jsonpickle, os, sys, stat
import signal
from select import select
import time
import datetime
import uuid
import logging
from flask import Blueprint, current_app, render_template, redirect, url_for, request, session, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

import psycopg2
import psycopg2.extras
import psycopg2.pool
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

from multiprocessing import Process, Pipe, get_context

from . import db, pgpool, cryptor, loglevel
from .models import User
from .util import jsonify_normalize, workerlist_normalize
from .process import dapgenerator

dap = Blueprint('dap', __name__)


@dap.route('/api/v1/dap/info', endpoint='info', methods=['GET'])
@login_required
def api_dapinfo():
    res = {}
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("select kind, count(*) from dap.entities group by kind union all select 'RIGHTS' as kind, count(*) from dap.rights;")
            res = { x['kind'] : x['count'] for x in  cursor.fetchall()}
    return jsonify(res)


@dap.route('/api/v1/dap/groups', endpoint='groups', methods=['POST'])
@login_required
def api_dapgroups():
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("select count(*) from dap.entities where kind = 'GROUP'")
            r = cursor.fetchone()
            total = r['count']
            cursor.execute("select id , kind, name from dap.entities where kind = 'GROUP' order by %s %s offset %s limit %s ;" % (
                int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'ctid',
                req['order'][0]['dir'] if len(req['order'])>0 else '',
                req['start'] if 'start' in req else 0,
                req['length'] if 'length' in req else 10
            ))
            data = [{"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "kind": "", "name": "{ All users without groups }"}] + jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    
@dap.route('/api/v1/dap/users', endpoint='users', methods=['POST'])
@dap.route('/api/v1/dap/users/<group>', endpoint='users', methods=['POST'])
@login_required
def api_dapusers(group = None):
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            data = []
            if group is None:
                cursor.execute("select count(*) from dap.entities where kind = 'USER'")
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select id , kind, name from dap.entities where kind = 'USER' order by %s %s offset %s limit %s ;" % (
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            elif group == 'nogroup':
                cursor.execute("select count(e.id) from dap.entities e left join dap.directory d on d.entity = e.id where e.kind = 'USER' and d.parent isnull;")
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select e.id, e.kind, e.name from dap.entities e left join dap.directory d on d.entity = e.id where e.kind = 'USER' and d.parent isnull order by %s %s offset %s limit %s ;" % (
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            else:
                cursor.execute("select count(e.id) from dap.sweep_down(%s) s join dap.entities e on e.id = s.entity where e.kind = 'USER';",(group,))
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select e.id, e.kind, e.name from dap.sweep_down('%s') s join dap.entities e on e.id = s.entity where e.kind = 'USER'  order by %s %s offset %s limit %s ;" % (
                    group,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    

@dap.route('/api/v1/dap/havings/<kind>', endpoint='havings', methods=['POST'])
@dap.route('/api/v1/dap/havings/<kind>/<user>', endpoint='havings', methods=['POST'])
@login_required
def api_havings(kind='any', user = None):
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            total = 0;
            data = []
            if user is None:
                pass
            else:
                if kind == 'any':
                    cursor.execute("select count(distinct id) from dap.havings(%s) ",(user,))
                else:
                    cursor.execute("select count(distinct id) from dap.havings(%s) where kind = %s",(user,kind,))
                r = cursor.fetchone()
                total = r['count']
                if kind == 'any':
                    cursor.execute("select h.id, h.kind, e.name, array_agg(h.permit) as rights  from dap.havings('%s') h join dap.entities e on e.id = h.id group by h.id, h.kind, e.name order by %s %s offset %s limit %s ;" % (
                    user,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                    ))
                else:    
                    cursor.execute("select h.id, h.kind, e.name, array_agg(h.permit) as rights  from dap.havings('%s') h join dap.entities e on e.id = h.id where kind = '%s' group by h.id, h.kind, e.name order by %s %s offset %s limit %s ;" % (
                    user,
                    kind,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                    ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    

@dap.route('/api/v1/dap/folders', endpoint='folders', methods=['POST'])
@login_required
def api_dapfolders():
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("select count(*) from dap.entities where kind = 'FOLDER'")
            r = cursor.fetchone()
            total = r['count']
            cursor.execute("select id , kind, name from dap.entities where kind = 'FOLDER' order by %s %s offset %s limit %s ;" % (
                int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'ctid',
                req['order'][0]['dir'] if len(req['order'])>0 else '',
                req['start'] if 'start' in req else 0,
                req['length'] if 'length' in req else 10
            ))
            data = [{"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "kind": "", "name": "{ All documents without folders }"}] + jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    
@dap.route('/api/v1/dap/documents', endpoint='documents', methods=['POST'])
@dap.route('/api/v1/dap/documents/<folder>', endpoint='documents', methods=['POST'])
@login_required
def api_dapdocuments(folder = None):
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            data = []
            if folder is None:
                cursor.execute("select count(*) from dap.entities where kind = 'DOCUMENT'")
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select id , kind, name from dap.entities where kind = 'DOCUMENT' order by %s %s offset %s limit %s ;" % (
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            elif folder == 'nofolder':
                cursor.execute("select count(e.id) from dap.entities e left join dap.directory d on d.entity = e.id where e.kind = 'DOCUMENT' and d.parent isnull;")
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select e.id, e.kind, e.name from dap.entities e left join dap.directory d on d.entity = e.id where e.kind = 'DOCUMENT' and d.parent isnull order by %s %s offset %s limit %s ;" % (
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            else:
                cursor.execute("select count(e.id) from dap.sweep_down(%s) s join dap.entities e on e.id = s.entity where e.kind = 'DOCUMENT';",(folder,))
                r = cursor.fetchone()
                total = r['count']
                cursor.execute("select e.id, e.kind, e.name from dap.sweep_down('%s') s join dap.entities e on e.id = s.entity where e.kind = 'DOCUMENT'  order by %s %s offset %s limit %s ;" % (
                    folder,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    

@dap.route('/api/v1/dap/shareholders/<kind>', endpoint='shareholders', methods=['POST'])
@dap.route('/api/v1/dap/shareholders/<kind>/<user>', endpoint='shareholders', methods=['POST'])
@login_required
def api_shareholders(kind='any', user = None):
    res = {}
    req = request.get_json()
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            total = 0;
            data = []
            if user is None:
                pass
            else:
                if kind == 'any':
                    cursor.execute("select count(distinct id) from dap.shareholders(%s) ",(user,))
                else:
                    cursor.execute("select count(distinct id) from dap.shareholders(%s) where kind = %s",(user,kind,))
                r = cursor.fetchone()
                total = r['count']
                if kind == 'any':
                    cursor.execute("select h.id, h.kind, e.name, array_agg(h.permit) as rights  from dap.shareholders('%s') h join dap.entities e on e.id = h.id group by h.id, h.kind, e.name order by %s %s offset %s limit %s ;" % (
                    user,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                    ))
                else:    
                    cursor.execute("select h.id, h.kind, e.name, array_agg(h.permit) as rights  from dap.shareholders('%s') h join dap.entities e on e.id = h.id where kind = '%s' group by h.id, h.kind, e.name order by %s %s offset %s limit %s ;" % (
                    user,
                    kind,
                    int(req['order'][0]['column'])+1 if len(req['order'])>0 else 'name',
                    req['order'][0]['dir'] if len(req['order'])>0 else '',
                    req['start'] if 'start' in req else 0,
                    req['length'] if 'length' in req else 10
                    ))
                data = jsonify_normalize(list(map(dict,cursor.fetchall())))
            res = {
                "draw": req['draw'] if 'draw' in req else 1,
                "recordsTotal": total,
                "recordsFiltered": total,
                "data": data
            }    
    return jsonify(res)
    

@dap.route('/api/v1/dap/effectiverights/<dapsubject>/<dapobject>', endpoint='effectiverights', methods=['GET'])
@login_required
def api_effectiverights(dapsubject, dapobject):
    res = []
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("select * from dap.effective_rights(%s,%s)",(dapsubject, dapobject,))
            res = jsonify_normalize(list(map(lambda x: x['effective_rights'],cursor.fetchall())))   
    return jsonify(res)


@dap.route('/api/v1/dap/random/<kind>/<int:limit>', endpoint='random', methods=['GET'])
@login_required
def api_daprandom(kind, limit = 5):
    res = []
    with pgpool.get_dbconn() as dbc:
        with dbc.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if kind.upper() == 'RIGHTPAIR':
                cursor.execute("select distinct * from ( select subject,object from dap.rights order by random() limit %s )q" % limit)
                res = jsonify_normalize(list(map(lambda x: [x['subject'],x['object']],cursor.fetchall())))   
            else:
                cursor.execute("select id from dap.entities where kind = '%s' order by random() limit %s" % (kind.upper(), limit))
                res = jsonify_normalize(list(map(lambda x: x['id'],cursor.fetchall())))   
    return jsonify(res)


@dap.route('/api/v1/dap/spawnproc', endpoint="spawnproc", methods=['GET'])
@dap.route('/api/v1/dap/spawnproc/<int:limit>', endpoint="spawnproc", methods=['GET'])
@login_required
def api_dapspawn(limit=500):
    try:
        global p
        ctx = get_context('fork')
        pd = current_app.config.get("pipedir", "/tmp")
        p = ctx.Process(target=dapgenerator, args=(pd,current_app.config['cf']['dbpool']['pg'],limit,))
        p.daemon = True
        p.start()
        pid = p.pid
    except Exception as e:
        current_app.logger.error(e)
        return 503, str(e) 
    try:
        os.mkfifo(os.path.join(pd,str(pid)))
    except:
        pass
    workers = session.get('workers',{})
    if isinstance(workers,list):
        session['workers'] = {}
    workers = session.get('workers',{})
    workers = workerlist_normalize(workers)
    session['workers'] = workers
    workers[str(pid)] = {
        "pid": int(pid),
        "pipe": os.path.join(pd,str(pid)),
        "started": datetime.datetime.now(),
        "local": True
    }
    session['workers'] = workers
    return jsonify({"pid": pid})

@dap.route('/api/v1/dap/askproc/<pid>', endpoint="askproc", methods=['GET'])
@login_required
def api_dapask(pid = None):
    res = {}
    if pid is not None:
        workers = session.get('workers')
        workers = workerlist_normalize(workers)
        session['workers'] = workers
        if pid in workers:
            _w = workers[pid]
            pipe = _w['pipe']
            data = None
            os.kill(int(pid), signal.SIGUSR1)   
            with open(pipe) as pf:
                _r,_,_ = select([pf],[],[],0.5)
                if len(_r) > 0:
                    data = pf.read()
            if data:
                res = json.loads(data)
    return jsonify(res)


@dap.route('/api/v1/dap/listproc', endpoint="listproc", methods=['GET'])
@login_required
def api_daplist(pid = None):
    res = {}
    workers = session.get('workers')
    workers = workerlist_normalize(workers)
    session['workers'] = workers
    return jsonify(workers)


#------------------------------------------------------------ views

@dap.route('/subjects', endpoint='subjects', methods=['GET'])
@login_required
def dapsubjects():
    return render_template('dap/subjects.html', segment='dap')


@dap.route('/objects', endpoint='objects', methods=['GET'])
@login_required
def dapobjects():
    return render_template('dap/objects.html', segment='dap')

@dap.route('/rights', endpoint='rights', methods=['GET'])
@login_required
def dapobjects():
    return render_template('dap/rights.html', segment='dap')

@dap.route('/generate', endpoint='generate', methods=['GET'])
@login_required
def dapobjects():
    return render_template('dap/generate.html', segment='dap')
