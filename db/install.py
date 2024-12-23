#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

import os, sys
import errno, traceback
import re, json, yaml, glob
import argparse
import time
from datetime import datetime

import psycopg2
import psycopg2.extras
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

_WD = os.path.dirname(os.path.realpath(__file__))

cf = {}

def _log(severity,msg):
    txt = "%s [%s] %s" % (datetime.today(),severity.upper(),msg)
    print(txt)

def _error(msg):
    _log('error',msg)

def _info(msg):
    _log('info',msg)

def _debug(msg):
    _log('debug',msg)

def sqload(path):
    _p = os.path.join(_WD,'structure',path)
    if os.path.isfile(_p):
        with open(_p,'rt',encoding="utf8") as f:
            return f.read()
    elif os.path.isdir(_p):
        return '\n\n'.join([sqload(x) for x in sorted(glob.glob(os.path.join(_p,"**","*.sql"), recursive=True))])
    else:
        raise ValueError("Invalid path")

def _fread(fn):
    v = None
    if os.path.isfile(os.path.join(_WD,fn)):
        with open(os.path.join(_WD,fn),'rt',encoding="utf8") as f:
            v = f.read().strip()
    return v

def _myversion():
    return _fread('.version')

def _mymemo():
    return _fread('.memo')

if __name__=="__main__":
    _info("Starting")
    st = time.time()
    cf = {
        'host': os.environ.get('PGHOST',None),
        'port': int(os.environ.get('PGPORT',5432)),
        'user': os.environ.get('PGUSER','veegodb'),
        'password': os.environ.get('PGPASSWORD',None),
        'superuser': os.environ.get('PGSUPERUSER','postgres'),
        'superpassword': os.environ.get('PGSUPERPASSWORD',None),
        'db': os.environ.get('PGDB','veegodb')
    }
    _info(str(cf))    
    if cf.get('host') is None:
        _error("""
            Environment not set. 
            Expected variables:
            PGHOST
            PGPORT
            PGUSER
            PGPASSWORD
            PGSUPERUSER
            PGSUPERPASSWORD
            PGDB
        """)
        sys.exit(0)
    schemas = []
    try:
        _info("PGS connection: ")
        dbsconn = psycopg2.connect(
            dbname='postgres',
            user=cf['superuser'],
            password=cf['superpassword'],
            host=cf['host'],
            port=cf['port'],
            connect_timeout=3
        )
        dbsconn.autocommit = True
        dbsconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        _info("..ok")
    except Exception as ex: 
        _error("Error on connection: " + str(ex))
        sys.exit(1)
    with dbsconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as scursor:
        _info("Check user objects:")
        try:
            scursor.execute("select * from pg_roles where rolname = %s",(cf['user'],))
            if scursor.rowcount < 1:
                scursor.execute("create role %s login createdb password '%s';" % (cf['user'],cf['password'],))
            for sql in [
                 "grant %s to %s;" % (cf['user'],cf['superuser'],)
                ,"grant azure_pg_admin to %s;" % (cf['user'],)
                ,"grant rds_superuser to %s;" % (cf['user'],)
                ,"alter role %s superuser;" % (cf['user'],)
            ]:
                try:
                    scursor.execute(sql);
                except:
                    pass
            _info("..ok")    
        except psycopg2.errors.UndefinedObject:
            pass
        except Exception as ex:
            _error("Error on role check: " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)

    try:
        _info("PG connection:")
        dbsconnu = psycopg2.connect(
            dbname='postgres',
            user=cf['user'],
            password=cf['password'],
            host=cf['host'],
            port=cf['port'],
            connect_timeout=3
        )
        dbsconnu.autocommit = True
        dbsconnu.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        _info("..ok")
    except Exception as ex: 
        _error("Error on connection: " + str(ex))
        sys.exit(1)
    with dbsconnu.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as ucursor:
        _info("Check db objects:")
        try:
            ucursor.execute("select * from pg_database where datname = %s",(cf['db'],))
            if ucursor.rowcount < 1:
                ucursor.execute("create database %s owner %s;" % (cf['db'],cf['user'],))
        except Exception as ex:
            _error("Error on db check: " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)
    try:
        dbconn = psycopg2.connect(
            dbname=cf['db'],
            user=cf['user'],
            password=cf['password'],
            host=cf['host'],
            port=cf['port'],
            connect_timeout=3
        )
        dbconn.autocommit = True
    except Exception as ex: 
        _error("Error on connection: " + str(ex))
        sys.exit(1)
    with dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        try:
            _info("Schema and extensions:")
            sql = sqload('schema.sql').replace('#USER#',cf['user'])
            schemas = ['.pre'] + re.findall(r' ([a-z]*) authorization',sql,re.MULTILINE) + ['.post']
            schemas.insert(max([schemas.index(x) for x in ['service','core','lib'] if x in schemas]) + 1, 'public') 
            sql += "\n\n" + sqload('extensions.sql').replace('#USER#',cf['user'])
            cursor.execute(sql)
            _info("DONE: Schema and extensions: ")
            _info("SCHEMAS: "+str(schemas))
        except Exception as ex:
            _error("Error on schema+ext: " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)
        _info("DONE: Check super objects")
    with dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        try:
            version = None
            try:
                cursor.execute("select * from core.version where module = 'base' order by major desc, minor desc, release desc limit 1")
                r = cursor.fetchone()
                version = "%s.%s.%s" % ( r['major'], r['minor'], r['release'] )
            except:
                pass
            myversion = _myversion()                   
            mymemo = _mymemo()
            if not myversion:
                _error("No distr version")
                sys.exit(1)
            if version:
                if version > myversion:
                    _error("Can`t downgrade from %s to %s " % (version, myversion))
                    sys.exit(1)
                else:
                    _info("Version shift from %s to %s " % (version, myversion))
                    for ufn in sorted(list(glob.glob(os.path.join(_WD,'updates','*.yml')))):
                        up = {
                             'REV': None
                            ,'CONDITION': None
                            ,'BODY': None
                            ,'MEMO': None
                        }
                        with open(ufn,'rt',encoding="utf8") as uf:
                            try:
                                up = yaml.safe_load(uf)
                                if not up or not 'REV' in up:
                                    raise ValueError("Invalid update structure")
                                up['REV'] = str(up['REV'])
                                cursor.execute("select 1 from core.version where module = 'update' and revision = %s",(up['REV'],))
                                if cursor.rowcount > 0:
                                    _info("Update: revision %s already installed, skipping." % up['REV'])
                                    continue
                                if up['CONDITION']:
                                    try:    
                                        cursor.execute(up['CONDITION']) 
                                        cond = False
                                        if cursor.rowcount > 0:
                                            r = cursor.fetchone()
                                            v = next(iter(r.values()))
                                            cond = False if v is None or v == False or v == 0 or str(v).lower() == 'false' else True
                                        if cond:
                                            cursor.execute(up['BODY'])
                                            cursor.execute("insert into core.version (module,revision,memo) values('update',%s,%s)", (up['REV'],up['MEMO'],))
                                    except Exception as ex:        
                                        _error("On: update: " + up['REV'] + ": " + up['MEMO'] + ": " + str(ex) + "\n" + traceback.format_exc())
                                        sys.exit(1)
                            except Exception as ex:
                                _error("Invalid update file: [%s] %s" % (ufn, str(ex)))
            else:
                _info("New install version %s" % (myversion))
        except Exception as ex: 
            _error("On: version and updates: " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)
        schema = None
        folder = None
        _info("Applying sructure:")
        try:
            dbconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
            for schema in schemas:
                for folder in ['.pre', 'tables', 'views', 'functions', 'data', 'triggers', 'alter', '.post']:
                    if os.path.isdir(os.path.join(_WD,'structure','schema',schema,folder)):
                        _info("Adding: " + os.path.join('schema',schema,folder))
                        sql = sqload(os.path.join('schema',schema,folder))
                        if sql:
                            cursor.execute(sql)
            [_vmj,_vmn,_vrl] = myversion.split('.')    
            cursor.execute("insert into core.version (module,major,minor,release,memo) values('base',%s,%s,%s,%s)", (_vmj,_vmn,_vrl,mymemo))
            dbconn.commit()            
            dbconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        except Exception as ex:           
            _error("On: structure: " + schema + ": " + folder + ": " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)
        et = time.time()    
    with dbsconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as scursor:
        _info("Revoking extra permissions:")
        try:
            scursor.execute("select * from pg_roles where rolname = %s",(cf['user'],))
            if scursor.rowcount > 0:
                for sql in [
                    "alter role %s nosuperuser;" % (cf['user'],)
                ]:
                    try:
                        scursor.execute(sql);
                    except:
                        pass
            _info("..ok")    
        except psycopg2.errors.UndefinedObject:
            pass
        except Exception as ex:
            _error("Error on revoke: " + str(ex) + "\n" + traceback.format_exc())
            sys.exit(1)
    _info("ALL DONE: Finished in " + str(et-st))

