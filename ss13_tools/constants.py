import sys

from .__version__ import __version__

USER_AGENT = f"ss13tools/{__version__} ({sys.platform}) Python {sys.version}"
POSITIVE_RESPONSES = ['y', 'yes', 'true', '1']
NEGATIVE_RESPONSES = ['n', 'no', 'false', '0']
