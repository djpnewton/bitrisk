#!/usr/bin/python
import sqlite3
import os

db_filename = 'bitcoin_events.db'
db_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), db_filename)

# connect db
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
    print 'tx', tx
    conn.execute('insert into txs (tx, processed) values (?, 0)', (tx,))
    conn.commit()

def process_block(block):
    print 'block', block
    conn.execute('insert into blocks (block, processed) values (?, 0)', (block,))
    conn.commit()

def check_db(conn):
    items = []
    txs = conn.execute('select * from txs where processed=0').fetchall()
    for tx in txs:
        conn.execute('update txs set processed=1 where tx=?', (tx[0],))
        items.append('tx: %s' % tx[0])
    blocks = conn.execute('select * from blocks where processed=0').fetchall()
    for block in blocks:
        conn.execute('update blocks set processed=1 where block=?', (block[0],))
        items.append('block: %s' % block[0])
    conn.commit()
    return items

def serve(port, host):
    from websocket_server import WebsocketServer
    from threading import Thread, Event
    import signal

    def service_thread(ws_server, evt):
        conn = sqlite3.connect(db_filename)
        while not evt.wait(5):
            res = check_db(conn)
            for item in res:
                print item
                ws_server.send_message_to_all(item)

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
        elif cmd == 'serve':
            if len(sys.argv) == 4:
                host = sys.argv[3]
                serve(int(arg), host)
        elif cmd == 'print':
            print_db(arg)
