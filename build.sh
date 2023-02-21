#!/bin/bash
if ! command -v python3 &> /dev/null
then
    echo "Python could not be found, installing..."
    apt install python3 python3-pip
fi

if ! command -v poetry &> /dev/null
then
    echo "Python Poetry could not be found, installing..."
    pip3 install poetry
fi

poetry install
poetry run pyinstaller --onefile ./entrypoint.py -n SS13Tools
