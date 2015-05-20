#!/usr/bin/python
import sqlite3

db_filename = 'bitcoin_events.db'

# connect db
conn = sqlite3.connect(db_filename)

# create tables
c = conn.cursor()
c.execute('''create table if not exists tx
        (tx text, processed int)''')
c.execute('''create table if not exists block
        (block text, processed int)''')
c.close()
conn.commit()

def process_tx(tx):
    conn.execute('insert into tx (tx, processed) values (?, 0)', tx)

def process_block(block):
    conn.execute('insert into block (block, processed) values (?, 0)', block)

def check_db(conn):
    items = []
    txs = conn.execute('select * from tx where processed=0')
    for tx in txs:
        conn.execute('update tx set processed=1 where tx=?', tx[0])
        items.append('tx: %s' % tx[0])
    blocks = conn.execute('select * from block where processed=0')
    for block in blocks:
        conn.execute('update block set processed=1 where block=?', block[0])
        items.append('block: %s' % block[0])
    conn.commit()
    return items

def serve(port):
    from websocket_server import WebsocketServer
    from threading import Thread, Event
    import signal

    def service_thread(ws_server, evt):
        conn = sqlite3.connect(db_filename)
        while evt.wait(5):
            res = check_db(conn)
            for item in res:
                ws_server.send_message_to_all(item)

    server = WebsocketServer(port)
    evt = Event()
    thread = Thread(target=service_thread, args=(server, evt))

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        exit(1) #TODO!!
        evt.set()
        server.server_close()
    signal.signal(signal.SIGINT, signal_handler)

    thread.start()
    server.run_forever()
    thread.join()

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        cmd = sys.argv[1]
        arg = sys.argv[2]
        if cmd == 'tx':
            process_tx(arg)
        elif cmd == 'block':
            process_block(arg)
        elif cmd == 'serve':
            serve(int(arg))
