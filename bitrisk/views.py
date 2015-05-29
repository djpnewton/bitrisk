from flask import url_for, session, request, render_template, redirect, flash, jsonify
import decimal
from bitcoinrpc.authproxy import JSONRPCException

import bitrisk
from bitrisk import app, config
from bitrisk import User
from bitrisk import bitcoind_rpc_connection
import utils

BETS = 'bets'

def current_user(session_key_name='id'):
    if session_key_name in session:
        uid = session[session_key_name]
        return User.query.get(uid)
    return None

def clear_user():
    if 'id' in session:
        session.pop('id', None)

def paginate_pagenums(row_count):
    page = request.args.get('page')
    if not page:
        page = 1
    try:
        page = int(page)
    except:
        page = 1
    max_pages = (row_count - 1) / config.main.paginate_row_count + 1
    pagenums = []
    if max_pages > 1:
        if page != 1:
            pagenums.append(1)
        if page > 5:
            pagenums.append('.')
        if page > 4:
            pagenums.append(page-3)
        if page > 3:
            pagenums.append(page-2)
        if page > 2:
            pagenums.append(page-1)
        pagenums.append(page)
        if page < max_pages - 1:
            pagenums.append(page + 1)
        if page < max_pages - 2:
            pagenums.append(page + 2)
        if page < max_pages - 3:
            pagenums.append(page + 3)
        if page < max_pages - 4:
            pagenums.append('.')
        if page != max_pages:
            pagenums.append(max_pages)
    return pagenums, page

@app.route('/', methods=('GET',))
def landing():
    return render_template('landing.html')

@app.route('/transactions')
def txs():
    return render_template('transactions.html')

@app.route('/bet')
def bet():
    address = bitcoind_rpc_connection.getnewaddress(BETS)
    print 'btc address:', address
    return redirect('/bet/%s' % address)

@app.route('/bet/<address>')
def bet_addr(address):
    try:
        if not bitcoind_rpc_connection.getaccount(address) == BETS:
            return 'invalid address'
    except JSONRPCException:
        return 'invalid address'
    qr = utils.qrcode(address)
    img_buf = utils.qrcode_png_buffer(qr)
    img_data = img_buf.getvalue()
    img_data_b64 = img_data.encode('base64').replace('\n', '')
    data_uri = 'data:image/png;base64,%s' % img_data_b64
    total = decimal.Decimal(bitcoind_rpc_connection.getbalance(BETS))
    print 'btc total:', total
    FOURPLACES = decimal.Decimal(10) ** -4
    print 'FOURPLACES:', FOURPLACES
    max_bet = total / 10
    print 'max_bet:', max_bet
    max_bet = max_bet.quantize(FOURPLACES)
    return render_template('bet.html', address=address, data_uri=data_uri, max_bet=max_bet)

@app.route('/bet/check/<txid>')
def bet_check(txid):
    #TODO: create table for processed txids
    #if controller.check_txid(txid):
    #   return blah blah blah
    return jsonify(result=False)

