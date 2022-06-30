import threading

class Queue:
    def __init__(self, maxsize: int = 0):
        self.maxsize = maxsize
        self.channels_being_processed = set()
        self.lock = threading.Lock()
        self.cv = threading.Condition(lock=self.lock)
        self.deterministic_exhaust_cv = threading.Condition()
        self.queue = []


    def _queue_not_full(self):
        return len(self.queue) < self.maxsize


    def put(self, path):
        with self.cv:
            self.queue.append(path)
            if len(self.queue) >= self.maxsize:
                self.cv.wait_for(self._queue_not_full)


    def get(self):
        with self.cv:
            for path in self.queue:
                start_channel = path[1]
                if start_channel not in self.channels_being_processed:
                    # Keep track of the start channel
                    self.channels_being_processed.add(start_channel)
                    self.queue.remove(path)
                    self.cv.notify()
                    return path
        return None


    def release(self, start_channel):
        with self.lock:
            print("Releasing channel", start_channel)
            self.channels_being_processed.remove(start_channel)


    def random_search_start(self):
        with self.deterministic_exhaust_cv:
            self.deterministic_exhaust_cv.notify_all()


    def wait_for_random_search_start(self):
        with self.deterministic_exhaust_cv:
            self.deterministic_exhaust_cv.wait()