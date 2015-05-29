# coding: utf-8

import os
from datetime import datetime, timedelta
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_kvsession import KVSessionExtension
from simplekv.db.sql import SQLAlchemyStore
from sqlalchemy import create_engine, MetaData
from flask_seasurf import SeaSurf
from flask_limiter import Limiter
import time
import random
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from bitcoind_config import read_default_config

import config

# create global config
config = config.Config(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.cfg'))
# create flask wsgi app
app = Flask(__name__, template_folder='templates')
app.debug = False
app.config.update({
    'SQLALCHEMY_DATABASE_URI': config.main.db_connection,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': config.main.secure_cookie,
    'PERMANENT_SESSION_LIFETIME': timedelta(minutes=config.main.session_lifetime),
    'SECRET_KEY': config.main.secret_key
})
# mandrill middlelware
if config.email.use_mandrill:
    app.config['MANDRILL_API_KEY'] = config.email.mandrill_api_key
    app.config['MANDRILL_DEFAULT_FROM'] = config.email.from_
# add sqlalchemy middleware
db = SQLAlchemy(app)
# add flask_kvsession middleware
app.config['SESSION_KEY_BITS'] = 128
engine = create_engine('sqlite:///bitrisk/sessions.sqlite')
metadata = MetaData(bind=engine)
store = SQLAlchemyStore(engine, metadata, 'kvstore')
metadata.create_all()
KVSessionExtension(store, app)
# add flask csrf middleware
csrf = SeaSurf(app)
# add rate limiting middleware
limiter = Limiter(app)
auth_limit = limiter.shared_limit("5/minute;1/second", scope="auth")

# connect to bitcoind
bitcoind_config = read_default_config()
testnet = ''
if bitcoind_config.has_key('testnet'):
    testnet = bitcoind_config['testnet']
rpc_user = bitcoind_config['rpcuser']
rpc_password = bitcoind_config['rpcpassword']
host = os.getenv('HOST', '127.0.0.1')
bitcoind_rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s8332"%(rpc_user, rpc_password, host, testnet))

# random number generator
cryptogen = random.SystemRandom()
house_edge = 0.01

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String)
    txid = db.Column(db.String, unique=True)
    processed = db.Column(db.Boolean)

class Payout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bet_id = db.Column(db.Integer, db.ForeignKey('bet.id'))
    processed = db.Column(db.Boolean)

def init_db():
    db.create_all()

@app.before_first_request
def init_all_on_first_request():
    init_db()

@app.before_request
def refresh_session():
    if session.has_key('gen_time'):
        gen_time = session['gen_time']
        lifetime = app.config['PERMANENT_SESSION_LIFETIME'].seconds
        if time.time() > gen_time + lifetime / 2:
            session.regenerate()
            session['gen_time'] = time.time()
    else:
        session['gen_time'] = time.time()

def user_create(email):
    user = User(email=email)
    db.session.add(user)
    db.session.commit()
    return user

def bet_add(addr, txid):
    # check if bet entry already exists
    bet = Bet.query.filter_by(txid=txid).first()
    if bet:
        return bet
    # create new entry
    bet = Bet(address=addr, txid=txid)
    db.session.add(bet)
    db.session.commit()
    return bet

def bet_process(bet):
    payout = None
    # create payout if bet wins
    num = cryptogen.random() - house_edge
    if num < 0.5:
        payout = Payout(bet_id=bet.id, processed=False)
        db.session.add(payout)
    # bet now processed
    bet.processed = 1
    db.session.add(bet)
    # commit changes and return payout
    db.session.commit()
    return payout




import bitrisk.views
