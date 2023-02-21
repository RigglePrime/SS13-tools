if (-not (Get-Command py -errorAction SilentlyContinue)) {
    Write-Host "Installing python with winget"
    winget install -e --disable-interactivity --id Python.Python.3.11
}
if (-not (Get-Command poetry -errorAction SilentlyContinue)) {
    Write-Host "Installing poetry"
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
}

Write-Host "Installing dependencies"
poetry install
Write-Host "Running pyinstaller"
poetry run pyinstaller --onefile .\ss13_tools\__main__.py -n SS13Tools
