from flask import url_for, session, request, render_template, redirect, flash, jsonify

import bitrisk
from bitrisk import app, config
from bitrisk import User

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
    if (current_user() is None):
        return render_template('landing.html')
    return redirect(url_for('home'))

@app.route('/transactions')
def txs():
    return render_template('transactions.html')

@app.route('/home')
def home():
    return render_template('home.html')
