#!/bin/sh

set -e

# start bitcoin server
echo write bitcoin.conf
if [ ! -d ~/.bitcoin ]; then
    mkdir ~/.bitcoin
fi
echo "testnet=1" > ~/.bitcoin/bitcoin.conf
echo "rpcuser=user" >> ~/.bitcoin/bitcoin.conf
echo "rpcpassword=test" >> ~/.bitcoin/bitcoin.conf
echo stop bitcoind
bitcoin-cli stop || echo ok
sleep 5s
echo start bitcoind
bitcoind -server -daemon -walletnotify="/vagrant/bitcoin_event.py tx %s" -blocknotify="/vagrant/bitcoin_event.py block %s"


cd /vagrant

export VENV_PATH=$HOME
echo setup python dependancies 
python setup_dependancies.py
export HOST=0.0.0.0
echo restart bitcoin_event.py
python run.py bitcoin_event.py serve stop || echo ok
python run.py bitcoin_event.py serve start
echo start bitrisk app
python run.py runserver.py debug
