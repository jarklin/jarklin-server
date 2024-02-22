# -*- coding=utf-8 -*-
r"""

"""


def run():
    import time
    import logging
    import multiprocessing
    from ..web import run as web_run
    from ..cache import run as cache_run

    web = multiprocessing.Process(target=web_run, name="web")
    cache = multiprocessing.Process(target=cache_run, name="cache")

    web.start()
    cache.start()

    try:
        while web.is_alive() and cache.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Caught KeyboardInterrupt. Shutting down...")
        if web.is_alive():
            web.terminate()
        if cache.is_alive():
            cache.terminate()
        web.join(timeout=10)
        cache.join(timeout=10)
    else:
        if web.is_alive():  # web alive, cache crashed
            web.terminate()
            logging.critical("jarklin-cache crashed")
        if cache.is_alive():  # cache alive, web crashed
            cache.terminate()
            logging.critical("jarklin-web crashed")
