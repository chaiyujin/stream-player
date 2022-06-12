import time


class timeit(object):
    def __init__(self, tag="timeit"):
        self.tag = tag

    def __enter__(self):
        self.ts = time.time()

    def __exit__(self, *args):
        self.te = time.time()
        print("<{}> cost {:.2f} ms".format(self.tag, (self.te - self.ts) * 1000))
        return False

    def __call__(self, method):
        def timed(*args, **kw):
            ts = time.time()
            result = method(*args, **kw)
            te = time.time()
            print("<{}> cost {:.2f} ms".format(method.__name__, (te - ts) * 1000))
            return result

        return timed


def format_time(msec: float) -> str:
    t = msec / 1000.0
    h = int(t / 3600)
    t -= h * 3600
    m = int(t / 60)
    t -= m * 60
    s = int(t)
    ms = t - s
    return f"{h:02d}:{m:02d}:{s:02d}" + f"{ms:.3f}"[1:]
