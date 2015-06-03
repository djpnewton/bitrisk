#!/usr/bin/python
import sqlite3
import os
import signal
import sys
from threading import Event
import decimal
import bitrisk

db_filename = 'bitrisk/db.sqlite'
db_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), db_filename)

# connect db
conn = sqlite3.connect(db_filename)
conn.row_factory = sqlite3.Row

# catch SIGINT
evt = Event()
def signal_handler(signal, frame):
    print 'bye bye'
    evt.set()
signal.signal(signal.SIGINT, signal_handler)

def tx_details(rpc_connection, txid):
    tx = rpc_connection.gettransaction(txid)
    if tx['confirmations'] == 0:
        print '  confirmations == 0'
        return
    total_in = decimal.Decimal(0)
    for details in tx['details']:
        if details['address'] == bet['address'] and details['category'] == 'receive':
            total_in += decimal.Decimal(details['amount'])
    print '  total_in:', total_in
    return total_in

def tx_parent_address(rpc_connection, txid):
    tx = rpc_connection.getrawtransaction(txid, 1)
    tx_parent = tx['vin'][0] #TODO: what about other vin's?
    txid_parent = tx_parent['txid']
    vout_parent = tx_parent['vout']
    tx = rpc_connection.getrawtransaction(txid_parent, 1)
    parent_address = tx['vout'][vout_parent]['scriptPubKey']['addresses'][0] #TODO: what about other addresses?
    print 'parent txid:', txid_parent
    print 'parent address:', parent_address
    return txid_parent, parent_address

def process_payout(rpc_connection, payout):
    print 'processing payout: id=%d, bet_id=%d, processed=%d' % (payout['id'], payout['bet_id'], payout['processed'])
    bet = conn.execute('select * from bet where id=?', (payout['bet_id'],)).fetchone()
    tx, total_in = tx_details(rpc_connection, bet['txid'])
    total_payout = total_in * 2
    print '  total_payout:', total_payout
    balance = rpc_connection.getbalance(bitrisk.BETS, 1)
    if balance >= total_payout:
        # get address bet was made from
        txid_parent, parent_address = tx_parent_address(bet['txid'])
        # send winnings
        txid = rpc_connection.sendfrom(bitrisk.BETS, parent_address, float(total_payout))
        conn.execute('update payout set txid=?, processed=1 where id=?', (txid, payout['id']))        
        conn.commit()
        print 'payout txid:', txid
    else:
        print '  balance not sufficient'

def process_refund(rpc_connection, refund):
    print 'processing refund: id=%d, bet_id=%d, processed=%d' % (refund['id'], refund['bet_id'], refund['processed'])
    bet = conn.execute('select * from bet where id=?', (refund['bet_id'],)).fetchone()
    tx, total_in = tx_details(rpc_connection, bet['txid'])
    balance = rpc_connection.getbalance(bitrisk.BETS, 1)
    if balance >= total_in:
        # get address bet was made from
        txid_parent, parent_address = tx_parent_address(bet['txid'])
        # send winnings
        txid = rpc_connection.sendfrom(bitrisk.BETS, parent_address, float(total_in))
        conn.execute('update payout set txid=?, processed=1 where id=?', (txid, payout['id']))        
        conn.commit()
        print 'refund txid:', txid
    else:
        print '  balance not sufficient'

def payouts():
    from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
    from bitrisk.bitcoind_config import read_default_config
    config = read_default_config()
    testnet = ''
    if config.has_key('testnet'):
        testnet = config['testnet']
    rpc_user = config['rpcuser']
    rpc_password = config['rpcpassword']
    host = os.getenv('HOST', '127.0.0.1')
    rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s8332"%(rpc_user, rpc_password, host, testnet))

    while not evt.wait(5):
        print 'process payouts/refunds'
        balance = rpc_connection.getbalance(bitrisk.BETS, 1)
        print 'balance:', balance
        print 'payouts:'
        payouts = conn.execute('select * from payout').fetchall()
        for payout in payouts:
            if not payout['processed']:
                process_payout(rpc_connection, payout)
        print 'refunds:'
        refunds = conn.execute('select * from refund').fetchall()
        for refund in refunds:
            if not refund['processed']:
                #TODO
                pass

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        cmd = sys.argv[1]
        from bitrisk.daemon import Daemon
        class BitcoinEventDaemon(Daemon):
            def run(self):
                payouts()
        daemon = BitcoinEventDaemon('/tmp/payouts-daemon.pid')
        if 'start' == cmd:
            daemon.start()
        elif 'stop' == cmd:
            daemon.stop()
        elif 'restart' == cmd:
            daemon.restart()
        elif 'foreground' == cmd:
            daemon.run()
    else:
        print "usage: %s serve start|stop|restart|foreground" % sys.argv[0]
        sys.exit(2)
