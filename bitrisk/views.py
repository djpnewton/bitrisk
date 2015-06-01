from flask import url_for, session, request, render_template, redirect, flash, jsonify
from bitcoinrpc.authproxy import JSONRPCException

import bitrisk
from bitrisk import app, config
from bitrisk import User, Bet, Payout, Refund
import utils

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
    address = bitrisk.bet_address_create()
    print 'btc address:', address
    return redirect('/bet/%s' % address)

@app.route('/bet/<address>')
def bet_addr(address):
    if not bitrisk.bet_valid_address(address):
        return 'invalid address'
    qr = utils.qrcode(address)
    img_buf = utils.qrcode_png_buffer(qr)
    img_data = img_buf.getvalue()
    img_data_b64 = img_data.encode('base64').replace('\n', '')
    data_uri = 'data:image/png;base64,%s' % img_data_b64
    max_bet = bitrisk.bet_max_amount()
    return render_template('bet.html', address=address, data_uri=data_uri, max_bet=max_bet)

@app.route('/bet/check/<addr>/<txid>')
def bet_check(addr, txid):
    image_win = '/static/images/winner/' + bitrisk.image_random('winner')
    image_lose = '/static/images/loser/' + bitrisk.image_random('loser')
    if not bitrisk.bet_valid_address(addr):
        return jsonify(result=False, msg='invalid address', image=image_lose)
    bet = bitrisk.bet_add(addr, txid)
    if bet.processed:
        return jsonify(result=False, msg='transaction already processed', image=image_lose)
    refund, payout = bitrisk.bet_process(bet)
    if refund:
        return jsonify(result=False, msg='bet too large - refund in progress', image=image_win)
    if payout:
        return jsonify(result=True, msg='', image=image_win)
    return jsonify(result=False, msg='', image=image_lose)

@app.route('/bets')
def bets():
    bets = Bet.query.all()
    return render_template('bets.html', bets=bets)

@app.route('/payouts')
def payouts():
    payouts = Payout.query.all()
    return render_template('payouts.html', payouts=payouts)

@app.route('/refunds')
def refunds():
    refunds = Refund.query.all()
    return render_template('refunds.html', refunds=refunds)
