import bitcoingw_db
import btc_payment_check

from uuid import uuid4
import time
import logging
from bottle import post, request, response, get, route, static_file 
import json
import requests

def get_logger():
    # Get named logger
    return logging.getLogger(__name__)

def setHeaders():
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token' 

# example: curl -d '{"pref_addr":"", "expiry":86400}' http://localhost:8229/bitcoingw/create_rec_addr
@route('/bitcoingw/create_rec_addr', method='POST')
def create_rec_address_api():
    setHeaders()
    postdata = request.body.read().decode('utf8')
    #print("postdata ", postdata)
    postjson = json.loads(postdata.replace("'", '"'))
    #print("postjson ", postjson)
    if 'expiry' not in postjson:
        return {"error": "Missing parameter"}
    pref_addr = ''
    if 'pref_addr' in postjson:
        pref_addr = postjson['pref_addr']
    expiry = postjson['expiry']
    return create_rec_address(pref_addr, expiry)

def create_rec_address(pref_addr, expiry):
    now = int(time.time())
    expiry_time = now + expiry
    return create_rec_address_int(pref_addr, now, expiry_time)

def create_rec_address_int(pref_addr, created_time, expiry_time):
    rec_addr = ''
    if len(pref_addr) > 0:
        # preferred address is given, check if it exists
        res = bitcoingw_db.find_rec_addr(pref_addr)
        if len(res) <= 0:
            # no such address
            return {"error": "Cannot use preferred address"}
        if res[0]['rec_addr'] != pref_addr:
            return {"error": "Internal error with preferred address"}
        rec_addr = pref_addr
    else:
        # create new address
        # TODO
        rec_addr = btc_payment_check.helper_get_real_current_btc_address()

        get_logger().info("Rec address created: " + str(rec_addr))
        # save address
        bitcoingw_db.add_rec_addr(rec_addr, created_time)
    # create new watch addr
    bitcoingw_db.add_watch_addr(rec_addr, created_time, expiry_time, 'btc', '')
    return {"addr": rec_addr, "valid_from": created_time, "valid_to": expiry_time }

# example: curl http://localhost:8229/bitcoingw/history/1KFHE7w8BhaENAswwryaoccDb6qcT6DbYY
@route('/bitcoingw/history/<address>', method = 'GET')
def get_history(address):
    time_to = time.time()
    time_from = time_to - 2 * 86400
    session = requests.Session()
    res = btc_payment_check.btc_check(session, address, time_from, time_to, min_confirmations = 3)
    #print(res)
    payments = []
    for p in res.payments:
        p2 = {
            'hash': p.tx_hash,
            'amount': p.amount,
            'timestamp': p.timestamp,
            #'from_addr': p.from_addr,
            'no_confirm': p.no_confirm
        }
        payments.append(p2)
    return {
        'address': address,
        'history': payments
    }

@route('/bitcoingw/get_watching_count', method = 'GET')
def get_watching_count():
    now = time.time()
    c_w = bitcoingw_db.get_current_watch_addr_count(now)
    c_r = bitcoingw_db.get_rec_addr_count()
    return {"addr_count": c_r, "watching": c_w}
