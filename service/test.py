import bitcoingw_init_db
import watcher_job
import api
import btc_payment_check

from uuid import uuid4
import time

def callback(addr):
    print("test: callback received for ", addr)
    history = api.get_history(addr)
    #print("history", history)
    if 'history' in history:
        print(" payments found:", len(history['history']))
        for p in history['history']:
            print("  pay", p['amount'], p['timestamp'], p['hash'])

print("now", time.time())
res = btc_payment_check.helper_get_real_current_btc_address()
print(res)

### bitcoingw_init_db.reinit_db()

addr_res = api.create_rec_address('', 86400)
#time1 = 1542900000
#addr_res = api.create_rec_address_int(time1, time1 + 86400)
#print(addr_res)
addr = addr_res["addr"]
print("New rec address:", addr, addr_res["valid_from"], addr_res["valid_to"])

# check with preferred addr
addr_res = api.create_rec_address(addr, 86400)
#print(addr_res)
addr = addr_res["addr"]
print("Repeated rec address:", addr, addr_res["valid_from"], addr_res["valid_to"])

# assume callback
callback(addr)

cnt = api.get_watching_count()
print("watching count", cnt)

watcher_job.start_job()    
watcher_job.stop_background()
