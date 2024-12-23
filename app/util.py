# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

from __future__ import unicode_literals
import base64, json, os, sys, stat
import time
import datetime
import uuid
import six
import multiprocessing as mp
from itertools import islice
from contextlib import contextmanager
from flask import current_app, g
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
import psycopg2
import psycopg2.extras
import psycopg2.pool
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)



class Cryptor:
    """
    FIXME:    
        Cipher is hardcoded to PKCS1_OAEP
        Hash is hardcoded to Crypto.Hash.SHA256
    """
    def __init__(self, app = None, keylength = 2048 ):
        self.default_keylength = keylength
        self.engine = None
        if app is not None:
            setapp(app)

    def setapp(self, app):
        self.app = app
        if app is not None and 'RSA' in app.config:
            self.public  = RSA.importKey(app.config['RSA']['public'])
            self.private = RSA.importKey(app.config['RSA']['private'])
        else:    
            random_generator = Random.new().read
            self.private = RSA.generate(self.default_keylength, random_generator) 
            self.public  = self.private.publickey()
        self.hash = Crypto.Hash.SHA256
        self.engine = PKCS1_OAEP.new(self.private, self.hash)
        self.keylength = Crypto.Util.number.size(self.public.n)
        self.keymod = Crypto.Util.number.ceil_div(self.keylength,8)
        self.blocksize = self.keymod - 2 * self.hash.digest_size - 2
        if self.blocksize < 8:
            raise ValueError("Cipher size too small")

    def publickey(self):
        if self.engine is None:
            raise ValueError("App engine not set")
        return self.public.exportKey('PEM')
    
    @staticmethod
    def staticencrypt(key, data):
        _key = RSA.importKey(key)
        _length = Crypto.Util.number.ceil_div(Crypto.Util.number.size(_key.n),8) - 2 * Crypto.Hash.SHA256.digest_size - 2
        _encryptor = PKCS1_OAEP.new(_key, Crypto.Hash.SHA256)
        res = b''
        i = iter(Cryptor.preformat(data))
        while(chunk := bytes(islice(i,_length))):
            res += _encryptor.encrypt(chunk)
        return res

    def encrypt(self, data):
        if self.engine is None:
            raise ValueError("App engine not set")
        res = b''
        i = iter(self.preformat(data))
        while(chunk := bytes(islice(i,self.blocksize))):
            res += self.engine.encrypt(chunk)
        return res

    def decrypt(self, data):
        if self.engine is None:
            raise ValueError("App engine not set")
        res = b''
        i = iter(data)
        while(chunk := bytes(islice(i,self.keymod))):
            res += self.engine.decrypt(chunk)
        return res
    
    @staticmethod
    def preformat(value):
        if isinstance(value, int):
            return six.binary_type(value)
        for str_type in six.string_types:
            if isinstance(value, str_type):
                return value.encode('utf8')
        if isinstance(value, six.binary_type):
            return value
        return value            

class Pgpool:
    def __init__(self, app = None):
        if app is not None:
            self.app = app

    def setapp(self, app):
        self.app = app

    @contextmanager
    def get_dbconn(self):
        conn = None
        if not hasattr(g,'pgpool') or g.pgpool is None:
            if 'cf' not in self.app.config or 'dbpool' not in self.app.config['cf']:
                raise ValueError("Invalid dbpool context")
            cf = self.app.config['cf']['dbpool']
            try:
                pool = psycopg2.pool.ThreadedConnectionPool(cf.get('minworkers',2), cf.get('maxworkers',4), **cf['pg'])
                setattr(g, 'pgpool', pool)
            except (Exception, psycopg2.DatabaseError) as ex:
                self.app.logger.error("DBD: "+str(ex))
                pass
        if hasattr(g,'pgpool'):
            try:
                conn = g.pgpool.getconn()
                conn.autocommit=True
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                yield conn
            finally:
                self.release_dbconn(conn)
        else:
            self.app.logger.error("Global pgpool not defined!")
            yield None

    def release_dbconn(self, conn):
        if conn is not None and hasattr(g,'pgpool') and g.pgpool is not None:
            g.pgpool.putconn(conn)

def jsonify_normalize(d, indent=None, sort_keys=False):
    def _process(x):
        if isinstance(x,list):
            for i, v in enumerate(x):
                x[i] = _process(v)
        elif isinstance(x,dict):
            for k,v in x.items():
                x[k] = _process(v)
        elif isinstance(x,datetime.datetime) or isinstance(x,datetime.date) or isinstance(x,datetime.time):
            x = x.isoformat()
        elif isinstance(x,datetime.timedelta):
            x = str(x)
        return x
    x = _process(d)
    return x

def pretty_jsonify(d, indent=None, sort_keys=False):
    x = _jsonify_normalize(d)
    return json.dumps(x, indent=indent, sort_keys=sort_keys) if x else None

def workerlist_normalize(workers):
    def pid_exists(pid):
        try:
            os.kill(pid,0)
        except OSError:
            return False
        else:
            return True
    children = mp.active_children()
    chpids = [c.pid for c in children]
    pd = current_app.config.get("pipedir", "/tmp")
    pipes = [f for f in os.listdir(pd) if f.isnumeric() and stat.S_ISFIFO(os.stat(os.path.join(pd,f)).st_mode)]
    res = {}
    for p,v in workers.items():
        pid = int(p)
        if pid in chpids:
            c = children[chpids.index(pid)]
            if c.is_alive():
                res[p] = v
            else:
                if p in pipes:
                    os.remove(os.path.join(pd,p))
            if p in pipes:
                pipes.remove(p)
        else:
            if p in pipes:
                if pid_exists(pid):
                    res[p] = v
                else:
                    os.remove(os.path.join(pd,p))
                pipes.remove(p)
    for p in pipes:
        if pid_exists(int(p)):
            res[p] = {
                "pid": int(p),
                "pipe": os.path.join(pd,p),
                "started": None,
                "local": False
            }
        else:
            os.remove(os.path.join(pd,p))
    return res            


