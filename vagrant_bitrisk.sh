#!/bin/sh

set -e

# start bitcoin server
if [ ! -d ~/.bitcoin ]; then
    mkdir ~/.bitcoin
fi
echo "testnet=1" > ~/.bitcoin/bitcoin.conf
echo "rpcuser=user" >> ~/.bitcoin/bitcoin.conf
echo "rpcpassword=test" >> ~/.bitcoin/bitcoin.conf
bitcoin-cli stop || echo ok
sleep 5s
bitcoind -server -daemon -walletnotify="/vagrant/bitcoin_event.py tx %s" -blocknotify="/vagrant/bitcoin_event.py block %s"


cd /vagrant

export VENV_PATH=$HOME
python setup_dependancies.py
export HOST=0.0.0.0
python run.py debug
