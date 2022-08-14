
import abc


class RangeReadable(abc.ABC):
    @abc.abstractmethod
    def read(self, offset, length):
        raise NotImplementedError()


class AbstractBuffer(RangeReadable):
    def __init__(self, source, cap, end=None):
        self.source = source
        self.size = min(250_000, cap)  # buffer at least 250k.
        self.cap = cap
        self.start_absolute = 0
        self.buffer = bytes()
        self.end = end  # May be set later when discovered

    def end_absolute(self):
        return self.start_absolute + len(self.buffer)


class DumbBytewiseBuffer(AbstractBuffer):
    def read(self, offset, length):
        if offset < 0 or length < 0:
            raise RuntimeError("Offset and length can't be negative.")
        elif length == 0:
            return b''

        if (offset < self.start_absolute) or (offset >= self.end_absolute()):
            return self.new_read(offset, length)
        else:
            return self.cache_read(offset, length)

    def new_read(self, offset, length):
        print(f"new_read({offset}, {length})")

        self.size = min(self.cap, self.size * 2)

        self.buffer = self.source(offset, self.size)
        self.start_absolute = offset

        if not self.end and (len(self.buffer) < self.size):
            print("end found.")
            self.end = self.start_absolute + len(self.buffer)

        out = self.buffer[:length]
        have = len(out)
        if length < have:
            raise RuntimeError("Grabbed too much data")
        elif length == have:
            return out
        elif self.end and (self.start_absolute + len(self.buffer)) >= self.end:
            print(f"new_read at end.")
            return out
        else:
            print(f"self.size={self.size}, self.buffer={len(self.buffer)}, self.start_absolute={self.start_absolute}, self.end={self.end}, have={have}")
            return out + self.new_read(offset + have, length - have)

    def cache_read(self, offset, length):
        print(f"cache_read({offset}, {length})")
        start_relative = offset - self.start_absolute

        out = self.buffer[start_relative:start_relative + length]
        have = len(out)
        if length < have:
            raise RuntimeError("Grabbed too much data")
        elif length == have:
            return out
        elif self.end and (self.start_absolute + len(self.buffer)) >= self.end:
            print(f"cache_read at end.")
            return out
        else:
            return out + self.new_read(offset + have, length - have)
