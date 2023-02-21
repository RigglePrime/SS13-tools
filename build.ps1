if (Get-Command poetry -errorAction SilentlyContinue) {
    poetry install
}
else {
    throw "Poetry not found"
}

.\.venv\Scripts\activate.ps1

if (Get-Command py -errorAction SilentlyContinue) {
    py -3 .\prepapre.py
}
elseif (Get-Command python -errorAction SilentlyContinue) {
    python .\prepapre.py
}
else {
    throw "Python not found"
}

poetry run pyinstaller --onefile ./entrypoint.py -n SS13Tools
