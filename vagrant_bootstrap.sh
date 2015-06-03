#!/bin/sh

set -e

apt-get install -y python-software-properties
add-apt-repository -y ppa:bitcoin/bitcoin
apt-get update
apt-get install -y bitcoind
apt-get install -y vim
apt-get install -y python-virtualenv
apt-get install -y python-dev
apt-get install -y zlib1g-dev
apt-get install -y git
apt-get install -y dos2unix

apt-get install -y curl
curl -sL https://deb.nodesource.com/setup | bash -
apt-get install -y nodejs
npm install -g bower
