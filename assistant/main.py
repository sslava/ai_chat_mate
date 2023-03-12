import os

from .telegram import *
from .chat import *


if __name__ == '__main__':
    import logging
    logging.root.setLevel(logging.INFO)
    if str(os.getenv("CLOUD")).lower() in {'1', 'true', 'yes'}:
        run_webhook()
    else:
        run_pooling()
