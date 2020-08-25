#!/bin/bash

if [ -d program ]
then
    rm -rf program
fi

if [[ ! "$(python3 -V)" =~ "Python 3" ]]
then
    echo "Install Python3 from https://www.python.org/downloads/"
    printf "Press any key to exit..."
    read
    exit 1
fi

if [[ `dpkg --list | grep python3-venv | wc -l` -eq 0 ]]
then
    sudo apt install python3-venv
fi

if [[ `dpkg --list | grep sox | wc -l` -eq 0 ]]
then
    sudo apt install sox
fi

deactivate
python3 -m pip install --user virtualenv
python3 -m venv env
source env/bin/activate

wget https://github.com/ELITR/Annotations/archive/master.zip
unzip master.zip -d program
rm master.zip

pip install -r program/Annotations-master/requirements.txt
deactivate