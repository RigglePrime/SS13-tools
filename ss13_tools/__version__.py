__version__ = 'UNKNOWN'
try:
    import importlib.metadata
    __version__ = importlib.metadata.version('ss13-tools')
except importlib.metadata.PackageNotFoundError:
    pass
