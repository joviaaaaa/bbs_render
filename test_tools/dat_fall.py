from datetime import datetime, timedelta
import psycopg2
import os
import re
from enum import Enum, IntEnum, auto

DATA_USER = os.environ['DATABASE_USER']
DATA_PASS = os.environ['DATABASE_PASS']
DATA_HOST = os.environ['DATABASE_HOST']
DATA_NAME = os.environ['DATABASE_NAME']

class atcl(IntEnum):
    id = 0
    article_count = auto()
    pub_date = auto()
    userid = auto()
    name = auto()
    article = auto()
    thread_id = auto()


try:
    cnn = psycopg2.connect(dbname=DATA_NAME,host=DATA_HOST,user=DATA_USER,password=DATA_PASS)
    cur = cnn.cursor()

    cur.execute("""SELECT * FROM article AS main_article
                   WHERE (thread_id, pub_date) in (
                      SELECT thread_id, max(pub_date) as to_date
                      FROM article AS tmp_article
                      GROUP BY thread_id
                      )""" )
    rows = cur.fetchall()
    dt_now = datetime.now()
    dt_falltime = dt_now - timedelta(minutes=30)
    for row in rows:
        #dt_diff = dt_now - row[atcl.pub_date]
        if(row[atcl.pub_date] < dt_falltime):
            print(dt_falltime)
            cur.execute("""DELETE FROM article WHERE thread_id = (%s)""", (row[atcl.thread_id],))
            cur.execute("""DELETE FROM thread WHERE id = (%s)""", (row[atcl.thread_id],))
            cnn.commit()

    cur.close()
    cnn.close()

except (psycopg2.OperationalError) as e:
    print (e)
