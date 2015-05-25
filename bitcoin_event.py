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

    def message_received(client, server, message):
        print 'message_received:', message
        cmds = message.split('|')
        for cmd in cmds:
            if cmd.startswith('addr='):
                address = cmd[5:]
                if server.watched_addresses.has_key(address):
                    server.watched_addresses[address].append(client)
                else:
                    server.watched_addresses[address] = [client]
            if cmd == 'blocks':
                server.block_watchers.append(client)

    def client_left(client, server):
        print 'client_left:', client
        addrs = []
        for key in server.watched_addresses:
            if client in server.watched_addresses[key]:
                addrs.append(key)
        for addr in addrs:
            clients = server.watched_addresses[addr]
            clients.remove(client)
            if not clients:
                del server.watched_addresses[addr]
        if client in server.block_watchers:
            server.block_watchers.remove(client)

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
                for details in tx['details']:
                    addr = details['address']
                    if ws_server.watched_addresses.has_key(addr):
                        def decimal_default(obj):
                            if isinstance(obj, decimal.Decimal):
                                return float(obj)
                            raise TypeError
                        msg = json.dumps(tx, default=decimal_default)
                        for client in ws_server.watched_addresses[addr]:
                            ws_server.send_message(client, msg)
            blocks = get_db_blocks(conn)
            for block in blocks:
                print 'block:', block
                for client in ws_server.block_watchers:
                    ws_server.send_message(client, block)

    server = WebsocketServer(port, host)
    server.watched_addresses = {}
    server.block_watchers = []
    server.set_fn_message_received(message_received)
    server.set_fn_client_left(client_left)
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
