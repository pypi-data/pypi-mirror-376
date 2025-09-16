__version__ = '1.0.0.dev35'

try:
    from importlib.metadata import version
    __version__ = version("solidkit")
except:
    pass
