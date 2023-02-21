if (Get-Command poetry -errorAction SilentlyContinue) {
    poetry install
}
else {
    throw "Python Poetry not found"
}

poetry run pyinstaller --onefile .\ss13_tools\__main__.py -n SS13Tools
