import logging
import threading
import time


logger = logging.getLogger(__name__)


class Daemon:
    def __init__(self):
        self._threads = []
        self._stop_threads = False
        pass


    def add_task(self, task):
        logger.info(f"Adding task {task}")
        self._threads.append(threading.Thread(target=task, args =(lambda : self._stop_threads,)))


    def run(self):
        logger.info("Start threads")
        for thread in self._threads:
            thread.daemon = True
            thread.start()
        while True:
            time.sleep(1)


    def stop(self):
        logger.info("Stop threads")
        self._stop_threads = True
