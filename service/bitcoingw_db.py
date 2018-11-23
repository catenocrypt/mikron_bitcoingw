import sqlite3
import time
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)

def get_logger():
    # Get named logger
    return logging.getLogger(__name__)

def get_db_name():
    return 'bitcoingw_db.db'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect():
    conn = sqlite3.connect(get_db_name())
    conn.row_factory = dict_factory
    return conn.cursor(), conn

def close(conn):
    conn.commit()
    conn.close()

def create_dbs():
    c, conn = connect()

    c.execute('''CREATE TABLE [rec_addr]
            (rec_addr text,
            created_time text,
            user_comment text)''')

    c.execute('''CREATE TABLE [watch_addr]
            (order_id text,
            rec_addr text,
            created_time text,
            expiry_time text,
            currency text,
            user_comment text,
            last_notif_hash text,
            last_notif_time text)''')

    get_logger().info("DB tables created")

    close(conn)

def add_rec_addr(rec_addr, created_time):
    c, conn = connect()
    sql_command = "INSERT INTO [rec_addr] VALUES ('" + \
        str(rec_addr) + "', " + \
        str(created_time) + ", '');"
    c.execute(sql_command)
    get_logger().info("receiver addr saved: " + str(rec_addr))
    close(conn)
    
def add_watch_addr(rec_addr, created_time, expiry_time, currency, user_comment):
    c, conn = connect()
    order_id = str(uuid4())
    #print ('order_id', order_id)
    now = int(time.time())
    sql_command = "INSERT INTO [watch_addr] VALUES ('" + \
        str(order_id) + "', '" + \
        str(rec_addr) + "', '" + \
        str(created_time) + "', '" + \
        str(expiry_time) + "', '" + \
        currency + "', '" + \
        user_comment + "', '', 0);"
    c.execute(sql_command)
    get_logger().info("new watch addr created, order_id " + str(order_id) + ", addr " + str(rec_addr) + ", " + str(now) + " - " + str(expiry_time))
    close(conn)
    return {"order_id": order_id}

def get_current_watch_addrs(now):
    c, conn = connect()
    c.execute("SELECT * FROM [watch_addr] WHERE expiry_time >= " + str(now) + ";")
    ret = c.fetchall()
    close(conn)
    return ret

def find_rec_addr(addr):
    c, conn = connect()
    c.execute("SELECT * FROM [rec_addr] WHERE rec_addr='" + str(addr) + "';")
    ret = c.fetchall()
    close(conn)
    return ret

def get_rec_addr_count():
    c, conn = connect()
    c.execute("SELECT COUNT(1) AS cnt FROM [rec_addr];")
    ret = c.fetchall()
    close(conn)
    #print(ret, len(ret))
    if len(ret) < 1:
        return 0
    if 'cnt' not in ret[0]:
        return 0
    #print(ret[0]['cnt'])
    return ret[0]['cnt']

def get_current_watch_addr_count(now):
    c, conn = connect()
    c.execute("SELECT COUNT(1) AS cnt FROM [watch_addr] WHERE expiry_time >= " + str(now) + ";")
    ret = c.fetchall()
    close(conn)
    #print(ret, len(ret))
    if len(ret) < 1:
        return 0
    if 'cnt' not in ret[0]:
        return 0
    #print(ret[0]['cnt'])
    return ret[0]['cnt']

def update_last_notif(order_id, hash, time):
    c, conn = connect()
    c.execute("UPDATE [watch_addr] SET last_notif_hash='" + str(hash) + "', last_notif_time=" + str(time) + " WHERE order_id='" + str(order_id) + "';")
    get_logger().info("Updated last notif: " + str(hash) + " " + str(time) + " for " + str(order_id))
    close(conn)
