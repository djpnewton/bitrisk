#!/bin/sh

set -e

cd /vagrant
export VENV_PATH=$HOME

echo stop bitcoin_event.py and payouts.py
python run.py bitcoin_event.py serve stop || echo ok
python run.py payouts.py stop || echo ok

if [ "$1" != "skip-bitcoind" ]; then
	# start bitcoin server
	echo write bitcoin.conf
	DATADIR=~/.bitcoin
	if [ ! -d $DATADIR ]; then
		mkdir $DATADIR
	fi
	echo "testnet=0" > $DATADIR/bitcoin.conf
	echo "rpcuser=user" >> $DATADIR/bitcoin.conf
	echo "rpcpassword=test" >> $DATADIR/bitcoin.conf
	echo stop bitcoind
	bitcoin-cli stop || echo ok
	sleep 5s
	echo start bitcoind
	bitcoind -server -daemon -datadir="$DATADIR" -walletnotify="/vagrant/bitcoin_event.py tx %s" -blocknotify="/vagrant/bitcoin_event.py block %s"
fi


echo setup python dependancies 
python setup_dependancies.py
export HOST=0.0.0.0
echo start bitcoin_event.py and payouts.py
python run.py bitcoin_event.py serve start
python run.py payouts.py start
echo start bitrisk app
python run.py runserver.py debug
