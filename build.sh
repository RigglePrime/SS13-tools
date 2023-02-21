#!/bin/bash
if ! command -v poetry &> /dev/null
then
    >&2 echo "Python Poetry could not be found"
    exit 1
fi

poetry install
poetry run pyinstaller --onefile ./entrypoint.py -n SS13Tools
