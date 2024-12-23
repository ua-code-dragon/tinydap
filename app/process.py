# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

import base64, json, jsonpickle, os, sys, stat
import signal
import time
import datetime
import names
import random
import uuid
import logging
from wonderwords import RandomSentence

import psycopg2
import psycopg2.extras
import psycopg2.pool
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


def dapgenerator(pd, dbcf, maxitems = 1000):
    n = 0

    nnf = 0
    nnd = 0
    nng = 0
    nnu = 0
    nnr = 0

    groups = []
    users = []
    docs = []
    folders = []
    rules = ['READ','WRITE','DELETE','CREATE']
    rs = RandomSentence()
    
    def dice(k):
        return random.randint(1,1000) > (1-k) * 1000.0

    def report(sig, frame):
        with open(os.path.join(pd,str(os.getpid())),'a') as pf:
            pf.write(json.dumps({
                "items": n,
                "progress": n*100.0/(maxitems*1.0),
                "count": {
                    "folder": nnf,
                    "document": nnd,
                    "group": nng,
                    "user": nnu,
                    "right": nnr
                }
            }))
    
    signal.signal(signal.SIGUSR1, report)

    with psycopg2.connect(**dbcf) as dbconn:
        dbconn.autocommit = True
        dbconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        with dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as dbc:

            dbc.execute("select id from dap.entities where kind = 'USER' order by random() limit 500")
            users = list(map(lambda x: x['id'], dbc.fetchall()))

            dbc.execute("select id from dap.entities where kind = 'GROUP' order by random() limit 15")
            groups = list(map(lambda x: x['id'], dbc.fetchall()))

            dbc.execute("select id from dap.entities where kind = 'DOCUMENT' order by random() limit 500")
            docs = list(map(lambda x: x['id'], dbc.fetchall()))

            dbc.execute("select id from dap.entities where kind = 'FOLDER' order by random() limit 15")
            folders = list(map(lambda x: x['id'], dbc.fetchall()))
                    
            dbc.execute("select max(name) from dap.entities where kind = 'GROUP' and name ~ 'GROUP[0-9]*'")
            gn = int(dbc.fetchone()['max'].replace('GROUP',''))
            
            dbc.execute("select max(name) from dap.entities where kind = 'FOLDER' and name ~ 'FOLDER[0-9]*'")
            fn = int((dbc.fetchone()['max'] or '0').replace('FOLDER',''))
            

            while n < maxitems:
                n += 1
                if dice(1.0/100.0):
                    uid = str(uuid.uuid4())
                    uname = names.get_full_name()
                    dbc.execute("insert into dap.entities(id,name,kind) values(%s, %s, 'USER');",(uid, uname))
                    users.append(uid)
                    nnu += 1
                    if len(groups) > 4:
                        for pg in random.sample(groups,random.randint(0,4)):
                            dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", (uid, pg))
                else:
                    uid = random.choice(users)
                if dice(1.0/10.0):
                    for uid in random.sample(users,random.randint(0,10)):
                        if len(docs) > 10:
                            for rd in random.sample(docs, random.randint(0,10)):
                                for r in random.sample(rules,random.randint(0,2)):
                                    dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", (uid, rd, r))
                                    nnr += 1
                                dbconn.commit()    
                        if len(folders) > 1:
                            for rd in random.sample(folders, random.randint(0,1)):
                                for r in random.sample(rules,random.randint(0,2)):
                                    dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", (uid, rd, r))
                                    nnr += 1
                                dbconn.commit()    
                if dice(1.0/100.0):
                    gn += 1
                    guid = str(uuid.uuid4())
                    gname = "GROUP%04d" % gn 
                    dbc.execute("insert into dap.entities(id,name,kind) values(%s, %s, 'GROUP');", (guid, gname))
                    dbconn.commit()
                    nng += 1
                    if len(users) > 4:
                        for pg in random.sample(users,random.randint(0,4)):
                            dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", (pg,guid))
                        dbconn.commit()    
                    if len(groups) > 1:
                        for pg in random.sample(groups,random.randint(0,1)):
                            dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", (guid, pg))
                        dbconn.commit()    
                    groups.append(guid)
                    if len(docs) > 10:
                        for rd in random.sample(docs, random.randint(0,3)):
                            for r in random.sample(rules,random.randint(0,2)):
                                dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", (guid, rd, r))
                            dbconn.commit()    
                    if len(folders) > 1:
                        for rd in random.sample(folders, random.randint(0,1)):
                            for r in random.sample(rules,random.randint(0,2)):
                                dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", (guid, rd, r))
                            dbconn.commit()    
                dn = 0
                mdn = random.randint(10,50)
                qu = []
                while dn < mdn:
                    dn += 1
                    did = str(uuid.uuid4())
                    s = dbc.mogrify("insert into dap.entities(id,name,kind) values(%s,%s, 'DOCUMENT');",(did,rs.sentence()))
                    nnd += 1
                    qu.append(s.decode())
                    if len(folders) > 3:
                        for pg in random.sample(folders,random.randint(0,3)):
                            s = dbc.mogrify("insert into dap.directory (entity, parent) values(%s, %s);", (did, pg))
                            qu.append(s.decode())
                    docs.append(did)
                    if len(qu) > 50:
                        dbc.execute(" ".join(qu))
                        dbconn.commit()
                        qu = []
                if len(qu) > 0:
                    dbc.execute(" ".join(qu))
                    dbconn.commit()
                if dice(1.0/100.0):
                    fn += 1
                    fname = "FOLDER%04d" % gn 
                    fuid = str(uuid.uuid4())
                    dbc.execute("insert into dap.entities(id,name,kind) values(%s,%s,'FOLDER');",(fuid,fname))
                    dbconn.commit()
                    nnf += 1
                    if len(docs) > 4:
                        for pg in random.sample(docs,random.randint(0,4)):
                            dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", (pg, fuid))
                        dbconn.commit()
                    if len(folders) > 1:
                        for pg in random.sample(folders,random.randint(0,1)):
                            dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", (fuid, pg))
                        dbconn.commit()    
                    folders.append(fuid)







