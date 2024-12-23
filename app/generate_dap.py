
import os, sys
import names
import uuid
import random
from wonderwords import RandomSentence


rs = RandomSentence()


def dice(k):
    return random.randint(1,1000) > (1-k) * 1000.0

maxlines = 1000
if len(sys.argv) > 1:
    maxlines = inr(sys.argv[1])

n = 0
gn = 0
fn = 0
groups = []
users = []
docs = []
folders = []
rules = ['READ','WRITE','DELETE','CREATE']

dbc.execute("select id from dap.entities where kind = 'USER' order by random() limit 500")
users = list(map(lambda x: x[0], dbc.fetchall()))

dbc.execute("select id from dap.entities where kind = 'GROUP' order by random() limit 15")
groups = list(map(lambda x: x[0], dbc.fetchall()))

dbc.execute("select id from dap.entities where kind = 'DOCUMENT' order by random() limit 500")
docs = list(map(lambda x: x[0], dbc.fetchall()))

dbc.execute("select id from dap.entities where kind = 'FOLDER' order by random() limit 15")
folders = list(map(lambda x: x[0], dbc.fetchall()))

while n < maxlines:
    n += 1
    if dice(1.0/100.0):
        uid = str(uuid.uuid4())
        uname = names.get_full_name()
        dbc.execute("insert into dap.entities(id,name,kind) values(%s, %s, 'USER');",[uid, uname])
        users.append(uid)
        if len(groups) > 4:
            for pg in random.sample(groups,random.randint(0,4)):
                dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", [uid, pg])
    else:
        uid = random.choice(users)
    if dice(1.0/10.0):
        for uid in random.sample(users,random.randint(0,10)):
            if len(docs) > 10:
                for rd in random.sample(docs, random.randint(0,10)):
                    for r in random.sample(rules,random.randint(0,2)):
                        dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", [uid, rd, r])
            if len(folders) > 1:
                for rd in random.sample(folders, random.randint(0,1)):
                    for r in random.sample(rules,random.randint(0,2)):
                        dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", [uid, rd, r])
    
    if dice(1.0/100.0):
        gn += 1
        guid = str(uuid.uuid4())
        gname = "GROUP%04d" % gn 
        dbc.execute("insert into dap.entities(id,name,kind) values(%s, %s, 'GROUP');",[guid, gname])
        if len(users) > 4:
            for pg in random.sample(users,random.randint(0,4)):
                dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", [pg,guid])
        if len(groups) > 1:
            for pg in random.sample(groups,random.randint(0,1)):
                dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", [guid, pg])
        groups.append(guid)
        if len(docs) > 10:
            for rd in random.sample(docs, random.randint(0,3)):
                for r in random.sample(rules,random.randint(0,2)):
                    dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", [guid, rd, r])
        if len(folders) > 1:
            for rd in random.sample(folders, random.randint(0,1)):
                for r in random.sample(rules,random.randint(0,2)):
                    dbc.execute("insert into dap.rights(subject, object, permit) values(%s,%s,%s)", [guid, rd, r])
    dn = 0
    mdn = random.randint(10,50)
    qu = []
    while dn < mdn:
        dn += 1
        did = str(uuid.uuid4())
        s = dbc.mogrify("insert into dap.entities(id,name,kind) values(%s,%s, 'DOCUMENT');",[did,rs.sentence()])
        qu.append(s.decode())
        if len(folders) > 3:
            for pg in random.sample(folders,random.randint(0,3)):
                s = dbc.mogrify("insert into dap.directory (entity, parent) values(%s, %s);", [did, pg])
                qu.append(s.decode())
        docs.append(did)
    if len(qu) > 0:
        dbc.execute(" ".join(qu))
    if dice(1.0/100.0):
        fn += 1
        fuid = str(uuid.uuid4())
        dbc.execute("insert into dap.entities(id,kind) values(%s,'FOLDER');",[fuid])
        if len(docs) > 4:
            for pg in random.sample(docs,random.randint(0,4)):
                dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", [pg, fuid])
        if len(folders) > 1:
            for pg in random.sample(folders,random.randint(0,1)):
                dbc.execute("insert into dap.directory (entity, parent) values(%s, %s)", [fuid, pg])
        folders.append(fuid)
    if n % 100 == 0:
        print("=== %s", n)







