# -*- coding=utf-8 -*-
r"""

"""
import time
import logging
import functools
import threading
import schedule


def catch_exceptions(cancel_on_failure=False):
    def decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception as error:
                logging.error(f"task {job_func.__name__} failed with ({type(error).__name__}", exc_info=error)
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return decorator


def run_continuously(scheduler: schedule.Scheduler, interval: int = 1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute, and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    def runner():
        fatally = 0

        while not cease_continuous_run.is_set():
            logging.debug("running pending jobs")
            try:
                scheduler.run_pending()
            except Exception as error:
                logging.error(f"error while executing scheduled jobs. (count: {fatally})", exc_info=error)
                fatally += 1
                if fatally > 3:
                    logging.critical(f"scheduled jobs failed to often. exiting", exc_info=error)
                    raise error
            else:
                fatally = 0
            logging.debug("waiting till next job run")
            time.sleep(interval)

    continuous_thread = threading.Thread(target=runner, name="scheduler")
    continuous_thread.start()
    return cease_continuous_run, continuous_thread
