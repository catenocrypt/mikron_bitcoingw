import logging
import btc_payment_check
import bitcoingw_db
import api

import time
import json
import threading
import requests

"""job delay in sec"""
delay = 30

logging.basicConfig(level=logging.INFO)

def get_logger():
    """ Get named logger """
    return logging.getLogger(__name__)

def job():
    now = int(time.time())
    #process_expired()
    process_btc_check()

def process_btc_check():
    now = int(time.time())
    pending_list = bitcoingw_db.get_current_watch_addrs(now)
    watch_cnt = len(pending_list)
    if watch_cnt <= 0:
        return
    #get_logger().info("Wathing " + str(watch_cnt) + " addresses")
    #print(pending_list)
    cnt_pay = 0
    cnt_notif = 0
    expiry_min = now + 10000000
    expiry_max = 0
    session = requests.Session()
    for p in pending_list:
        if 'currency' in p and p['currency'].upper() == 'BTC':
            #print(p)
            addr = p['rec_addr']
            time_from = float(p['created_time'])
            time_to = float(p['expiry_time'])

            if time_to > expiry_max:
                expiry_max = time_to
            if time_to < expiry_min:
                expiry_min = time_to

            #print("Pending", "BTC to", addr, "since", time_from, "to max", time_to)
            res = btc_payment_check.btc_check(session, addr, time_from, time_to, 3)
            #res.print()
            #print("age", now - int(p['created_time']))
            # Condition: if it has been payed in full, confirmed
            if (res != None) and (res.sum_confirmed > 0) and (len(res.payments) > 0):
                last_hash = res.payments[0].tx_hash
                #get_logger().info("Incoming payment detected; confirmed amount " + str(res.sum_confirmed) + " to address " + addr + " last hash " + last_hash)
                order_id = p['order_id']
                #print("last_hash", p['last_notif_hash'], last_hash, "!")
                if (p['last_notif_hash'] == last_hash):
                    #get_logger().info("This tx hash already been notified " + str(p['last_notif_hash']) + " " + str(p['last_notif_time']))
                    notif_time = time.time()  # unnecessary placeholder line
                else:
                    get_logger().info("Incoming payment detected; not yet notified; confirmed amount " + str(res.sum_confirmed) + " to address " + addr + " last hash " + last_hash)
                    notif_time = time.time()
                    do_notify(addr)
                    bitcoingw_db.update_last_notif(order_id, last_hash, notif_time)
                    cnt_notif = cnt_notif + 1
                cnt_pay = cnt_pay + 1
            # small sleep to not overload APIs
            time.sleep(0.05)
    get_logger().info("Watch addrs: " + str(watch_cnt) + " expiry range: " + str(int(expiry_min) - now) + " - " + str(int(expiry_max) - now) + ", found " + str(cnt_pay) + " payments, notified " + str(cnt_notif) + " new")

def do_notify(addr):
    # TODO call web hook
    print("TODO Callback for ", addr)
    history = api.get_history(addr)
    #print("history", history)
    if 'history' in history:
        print(" payments found:", len(history['history']))
        for p in history['history']:
            print("  pay", p['amount'], p['timestamp'], p['hash'])

def start_job():
    get_logger().info("Starting job")
    next_update = time.time()
    while getattr(threading.currentThread(), "do_run", True):
        now = time.time()
        #print("now", now)
        if (now >= next_update):
            job()
            next_update = next_update + delay
        time.sleep(1)

watcher_thread = None
def start_background():
    watcher_thread = threading.Thread(target=start_job)
    watcher_thread.start()

def stop_background():
    watcher_thread.do_run = False
    watcher_thread.join()
