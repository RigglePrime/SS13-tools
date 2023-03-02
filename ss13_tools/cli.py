def run():
    """Runs the main, intended to be used with scripts"""
    from ss13_tools import __main__  # noqa: F401 # pylint: disable=import-outside-toplevel,unused-import


def log_buddy():
    """Runs the main for LogBuddy, intended to be used with scripts"""
    from ss13_tools.log_buddy.__main__ import main  # noqa: F401 # pylint: disable=import-outside-toplevel,unused-import
    main()


def centcom():
    """Runs the main for Centcom, intended to be used with scripts"""
    from ss13_tools.centcom.__main__ import main  # noqa: F401 # pylint: disable=import-outside-toplevel,unused-import
    main()
