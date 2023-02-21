#!/bin/bash

if ! command -v python3 &> /dev/null
then
    >&2 echo "Python could not be found"
    exit 1
fi

if ! command -v poetry &> /dev/null
then
    >&2 echo "Python Poetry could not be found"
    exit 1
fi

poetry install
source ./.venv/Scripts/activate
python3 ./prepapre.py
poetry run pyinstaller --onefile ./entrypoint.py -n SS13Tools
