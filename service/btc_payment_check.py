import payment_result

import requests
import json
import datetime
import time

# Checks incoming BTC transactions to a given address, within a time range
# Returns a PaymentResult
def btc_check(session, address, time_from, time_to, min_confirmations = 3):
    return btc_check_mock(address, time_from, time_to, min_confirmations)  # TODO

    cur_block_height = __getBlockHeight(session)
    #print("Checking BTC", address, "time range", time_from, time_to.__str__(), cur_block_height)
    url = 'https://blockchain.info/en/rawaddr/' + address
    #print('url', url)
    response = session.get(url)
    #print(response)
    #print(response.status_code)
    payments = []
    if response.status_code != 200:
        print("Error", response.status_code, "cont", response.content)
        return payment_result.PaymentResult('BTC', time_from, time_to)
    #print(response.content)
    #data = json.load(response.content)
    data = response.json()
    #print data
    #print("final balance:", data['final_balance'])
    #print(len(data['txs']))
    for tx in data['txs']:   #reversed(data['txs']):
        p = __checkTransaction(tx, address, time_from, time_to, cur_block_height)
        if p is not None:
            payments.append(p)
    # compute sums
    sum_confd = 0
    sum_nonconfd = 0
    for p in payments:
        sum_nonconfd = sum_nonconfd + p.amount
        if (p.no_confirm >= min_confirmations):
            sum_confd = sum_confd + p.amount
    res = payment_result.PaymentResult('BTC', time_from, time_to, sum_confd, sum_nonconfd, payments)
    #res.print()
    return res

def btc_check_mock(address, time_from, time_to, min_confirmations = 3):
    t1 = int(time_from)
    t2 = int(int(t1 % 11) * int(t1 % 13))
    time_delta = int(30 + t2 * 10)
    now = int(time.time())
    t = int(time_from) + time_delta
    payments = []
    pay_sum = 0
    cnt = 0
    while (t < now) and (cnt < 30):
        #print(cnt, t, now, t-now)
        dummy_tx_time = t
        dummy_tx_hash = "hash_" + str(dummy_tx_time) + "_" + str(cnt) + "_" + str(time_delta)
        dummy_tx_amount = 0.001 * (time_delta + cnt)
        p1 = payment_result.PaymentInfo(dummy_tx_hash, dummy_tx_amount, dummy_tx_time, address, "dummyFromAddr", 8)
        payments.insert(0, p1)  # reverse order
        pay_sum = pay_sum + p1.amount
        t = t + time_delta
        cnt = cnt + 1
    return payment_result.PaymentResult('BTC', time_from, time_to, pay_sum, pay_sum, payments)

def __checkTransaction(tx, address, time_from, time_to, cur_block_height):
    #print(tx)
    no_confirm = 0
    tx_hash = ''
    if ('hash' in tx):
        tx_hash = tx['hash']
    if 'block_height' in tx:
        block = tx['block_height']
        #print('block_height:', block)
        no_confirm = cur_block_height - block + 1
    time = tx['time']
    #print('time:', time, time_from, time_to)
    if time <= time_from:
        # old transaction, already checked, ignore
        return None
    if time > time_to:
        # future transactrion, already checked, ignore
        return None
    from_addr = None
    
    #print("spent")
    for inp in tx['inputs']:
        if ('prev_out' in inp) and ('spent' in inp['prev_out']):
            #print inp['prev_out']['spent']
            if inp['prev_out']['spent']:
                from_addr = inp['prev_out']['addr']
                #print(from_addr)
                if from_addr == address:
                    #print(inp)
                    value = inp['prev_out']['value']
                    #spent_sum = spent_sum + value/100000000
                    #print('spent value:', value, 'spent total', spent_sum)
    #print("received")
    is_in_out = False
    out_amount = 0
    for out in tx['out']:
        #print(out['spent'])
        #print(out['addr'])
        if ('addr' in out) and (out['addr'] == address):
            is_in_out = True
            #print(out)
            value = out['value']
            out_amount = value
            #recd_sum = recd_sum + value/100000000
            #print('recd value:', value, 'recd total', recd_sum)
    #print('result:', tx['result'], 'spent total', spent_sum, 'recd total', recd_sum)
    if is_in_out:
        return payment_result.PaymentInfo(tx_hash, out_amount/100000000, time, address, from_addr, no_confirm)
    return None
    
def __getBlockHeight(session):
    url = 'https://blockchain.info/en/q/getblockcount'
    return int(session.get(url).content)

# get a real BTC address, recently used as a recipient
def helper_get_real_current_btc_address():
    # get current block height
    session = requests.Session()
    block_height = int(__getBlockHeight(session))
    #print("block_height", block_height)
    target_block_height = block_height - 3
    # get latest block hashes
    starttime = (int(float(time.time())) - 2 * 3600) * 1000
    url = "https://blockchain.info/blocks/" + str(starttime) + "?format=json"
    #print(url)
    response = session.get(url)
    #print(response)
    #print(response.status_code)
    if response.status_code != 200:
        return "ERROR_status_" + response.status_code
    #print(response.content)
    #data = json.load(response.content)
    data = response.json()
    #print(data)
    if 'blocks' not in data:
        return "ERROR_no_blocks"
    target_block_hash = ''
    for b in data['blocks']:
        if ('height' in b) and ('hash' in b) and (b['height'] == target_block_height):
            target_block_hash = b['hash']
    print("target_block_hash", target_block_hash)
    # get target block
    url = "https://blockchain.info/rawblock/" + str(target_block_hash)
    #print(url)
    response = session.get(url)
    #print(response)
    #print(response.status_code)
    if response.status_code != 200:
        return "ERROR_status_" + response.status_code
    #print(response.content)
    #data = json.load(response.content)
    data = response.json()
    #print(data)
    if ('tx' in data) and (len(data['tx']) >= 0):
        #print(data['tx'][0])
        if 'out' in data['tx'][0]:
            #print(data['tx'][0]['out'])
            if len(data['tx'][0]['out']) >= 0:
                #print(data['tx'][0]['out'][0])
                if 'addr' in data['tx'][0]['out'][0]:
                    return data['tx'][0]['out'][0]['addr']
    return "ERROR_could_not_retrieve_addr"
