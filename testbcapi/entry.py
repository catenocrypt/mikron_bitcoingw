from threading import Thread
from uuid import uuid4
import time
import logging
import bottle
import json
import requests

cfg = {
        'listen_host': 'localhost',
        'listen_port': 8229,
        'xpub': 'xpub6Cxb2AMw38gNBhPbVSaoTw8mWd39uL6j5RLZVAQhQw4qtKUdZLgaYkD34p6vQ6AqoxDWPexirHfRLQJyQR419NKrp4HvewLhFqGWYdj7zpW'
    }
debug_lines = ["(payment notifications come here)"]

def setHeaders():
    bottle.response.content_type = 'application/json'
    bottle.response.headers['Access-Control-Allow-Origin'] = '*'
    bottle.response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    bottle.response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token' 

@bottle.route('/testbcreceive/callback', method='POST')
def test_blockchaincom_callback():
    setHeaders()
    postdata = bottle.request.body.read().decode('utf8')
    #print("postdata ", postdata)
    postjson = json.loads(postdata.replace("'", '"'))
    print("postjson ", postjson)
    resp = "NOT_OK"
    secret = ''
    if 'secret' in postjson:
        secret = postjson['secret']
    if 'transaction_hash' in postjson and 'address' in postjson and 'confirmations' in postjson and 'value' in postjson:
        confirmations = int(postjson['confirmations'])
        if confirmations < 3:
            print("Not enough confirmations!", confirmations)
        else:
            # ACCEPTED
            resp = "*ok*"   # proper response
            msg = "Payment received, amount " + str(postjson['value']) + ", conf's " + str(confirmations) + ", to_addr " + str(postjson['address']) + ", tx_hash " + str(postjson['transaction_hash']) + ", secret " + str(secret) + " ."
            print("Msg", msg)
            debug_lines.insert(0, msg)
            cnt = 1
            for l in debug_lines:
                print(cnt, l)
                cnt = cnt + 1
    return resp

@bottle.route('/testbcreceive/test.html', method='GET')
def get_file_index():
    return bottle.static_file("test.html", root="testbcapi/")

@bottle.route('/testbcreceive/debuglines', method='GET')
def test_blockchaincom_debug_linex():
    resp = ''
    for l in debug_lines:
        resp = l + '\r\n' + resp
    return resp

listen_host = cfg['listen_host']
listen_port = cfg['listen_port']
bottle.run(host = listen_host, port = listen_port, debug = True)
