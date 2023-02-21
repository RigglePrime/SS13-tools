if (-not (Get-Command poetry -errorAction SilentlyContinue)) {
    throw "Python Poetry not found"
}

poetry install
poetry run pyinstaller --onefile .\ss13_tools\__main__.py -n SS13Tools
