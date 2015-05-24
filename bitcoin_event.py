#!/usr/bin/python
import sqlite3
import os
from threading import Lock

db_filename = 'bitcoin_events.db'
db_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), db_filename)

# connect db
db_lock = Lock()
conn = sqlite3.connect(db_filename)

# create tables
c = conn.cursor()
c.execute('''create table if not exists txs
        (tx text, processed int)''')
c.execute('''create table if not exists blocks
        (block text, processed int)''')
c.close()
conn.commit()

def process_tx(tx):
    with db_lock:
        conn.execute('insert into txs (tx, processed) values (?, 0)', (tx,))
        conn.commit()

def process_block(block):
    with db_lock:
        conn.execute('insert into blocks (block, processed) values (?, 0)', (block,))
        conn.commit()

def get_db_txs(conn):
    with db_lock:
        items = []
        txs = conn.execute('select * from txs where processed=0').fetchall()
        for tx in txs:
            conn.execute('update txs set processed=1 where tx=?', (tx[0],))
            items.append(tx[0])
        conn.commit()
        return items

def get_db_blocks(conn):
    with db_lock:
        items = []
        blocks = conn.execute('select * from blocks where processed=0').fetchall()
        for block in blocks:
            conn.execute('update blocks set processed=1 where block=?', (block[0],))
            items.append(block[0])
        conn.commit()
        return items

def serve(port, host):
    from websocket_server import WebsocketServer
    from threading import Thread, Event
    import signal

    def service_thread(ws_server, evt):
        from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
        from bitrisk.bitcoind_config import read_default_config
        import json
        import decimal
        config = read_default_config()
        testnet = ''
        if config.has_key('testnet'):
            testnet = config['testnet']
        rpc_user = config['rpcuser']
        rpc_password = config['rpcpassword']
        rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s8332"%(rpc_user, rpc_password, host, testnet))
        
        conn = sqlite3.connect(db_filename)
        while not evt.wait(5):
            txs = get_db_txs(conn)
            for tx in txs:
                print 'tx:', tx
                tx = rpc_connection.gettransaction(tx)
                def decimal_default(obj):
                    if isinstance(obj, decimal.Decimal):
                        return float(obj)
                    raise TypeError
                ws_server.send_message_to_all(json.dumps(tx, default=decimal_default))
            blocks = get_db_blocks(conn)
            for block in blocks:
                print 'block:', block
                ws_server.send_message_to_all(block)

    server = WebsocketServer(port, host)
    evt = Event()
    thread = Thread(target=service_thread, args=(server, evt))

    thread.start()
    server.run_forever() # catches and exits on SIGINT
    evt.set() # stop service_thread
    thread.join()

def print_db(table):
    if table != 'txs' and table != 'blocks':
        print 'table %s does not exist' % table
        return
    if table == 'txs':
        txs = conn.execute('select * from txs').fetchall()
        print 'txs (%d)' % len(txs)
        for tx in txs:
            print '  ', tx
    if table == 'blocks':
        blocks = conn.execute('select * from blocks').fetchall()
        print 'blocks (%d)' % len(blocks)
        for block in blocks:
            print '  ', block

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        cmd = sys.argv[1]
        arg = sys.argv[2]
        if cmd == 'tx':
            process_tx(arg)
        elif cmd == 'block':
            process_block(arg)
        elif cmd == 'print':
            print_db(arg)
        elif cmd == 'serve':
            from bitrisk.daemon import Daemon
            class BitcoinEventDaemon(Daemon):
                def run(self):
                    host = os.getenv('HOST', '127.0.0.1')
                    serve(8888, host)
            daemon = BitcoinEventDaemon('/tmp/bitcoin-event-daemon.pid')
            if 'start' == arg:
                daemon.start()
            elif 'stop' == arg:
                daemon.stop()
            elif 'restart' == arg:
                daemon.restart()
            elif 'foreground' == arg:
                daemon.run()
            else:
                print "usage: %s serve start|stop|restart|foreground" % sys.argv[0]
                sys.exit(2)
            sys.exit(0)
