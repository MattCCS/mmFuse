
import abc
import threading
import time


class RangeReadable(abc.ABC):
    @abc.abstractmethod
    def read(self, offset, length):
        raise NotImplementedError()


class AbstractBuffer(RangeReadable):
    def __init__(self, source, cap, end=None):
        self.source = source
        self.size = min(250_000, cap)  # buffer at least 250k.  # TODO: unused
        self.cap = cap  # TODO: unused
        self.start_absolute = 0
        self.buffer = bytes()
        self.end = end  # May be set later when discovered

    def end_absolute(self):
        return self.start_absolute + len(self.buffer)


def start_background_load(buffer, block, blocksize, blocks):
    t = threading.Thread(target=background_load, args=(buffer, block, blocksize, blocks))
    t.start()


def background_load(buffer, block, blocksize, blocks):
    offset = block * blocksize
    length = blocks * blocksize
    print(f"[r] Async read of block {block}, blocks {blocks}")
    buffer.load_async(buffer.source(offset, length), block, blocks)


class BlockwiseBuffer(AbstractBuffer):
    def __init__(self, source, size, end=None, blocksize=2_000_000, cache_limit=20, prefetch_blocks=2):
        super().__init__(source, size, end=end)
        self.blocksize = blocksize
        self.cache_limit = cache_limit
        self.prefetch_blocks = prefetch_blocks
        self.cache = {}
        self.stored = 0
        self.hits = {}
        self.requests = set()

    def load_async(self, bytez, start_block, blocks):
        print(f"[async receiving {start_block}, {blocks}]")
        for idx in range(blocks):
            block = (start_block + idx)
            self.cache[block] = bytez[idx * self.blocksize:(idx + 1) * self.blocksize]
            self.hits[block] = time.monotonic()
            self.requests.remove(block)

    def block(self, byte):
        return int(byte / self.blocksize)

    def next_block(self, byte):
        return self.block(byte) + 1

    def blocks(self, offset, length):
        return list(range(self.block(offset), self.block(offset + length) + 1))

    def cached_blocks(self):
        return len(self.cache)

    def worst_block(self):
        return min(self.hits.keys(), key=lambda k: self.hits[k])

    def invalidate(self, block=None):
        if block is None:
            block = self.worst_block()
        print(f"[i] invalidating {block}")
        del self.cache[block]
        del self.hits[block]

    def prefetch(self, offset):
        for idx in range(self.prefetch_blocks):
            next_block = (self.next_block(offset) + idx)
            if next_block not in self.cache and next_block not in self.requests:
                print(f"(starting background load for: {next_block})")
                start_background_load(self, next_block, self.blocksize, 1)
                self.requests.add(next_block)

    def read(self, offset, length):
        print(self.hits)

        if offset < 0 or length < 0:
            raise RuntimeError("Offset and length can't be negative.")
        elif length == 0:
            return b''

        if self.cached_blocks() >= self.cache_limit:
            self.invalidate()

        block = self.block(offset)
        if block not in self.cache and block not in self.requests:
            return self.new_read(offset, length)
        elif block in self.requests:
            print(f"[ ] Waiting for pending request...")
            self.prefetch(offset)
            for _ in range(70):
                time.sleep(0.1)
                if block in self.cache:
                    return self.cache_read(offset, length)
            else:
                print(f"[!] Cache took too long to populate!")
                raise RuntimeError("cache delay")
        else:
            print(f"read (DEBUG) offset={offset}, length={length}")
            return self.cache_read(offset, length)

    def new_read(self, offset, length):
        print(f"new_read({offset}, {length})")

        block = self.block(offset)
        print(f"[r] Sync read of block {block}")
        read = self.source(block * self.blocksize, self.blocksize)
        self.cache[block] = read
        self.hits[block] = time.monotonic()

        if not self.end and (len(read) < self.blocksize):
            # print("end found.")
            self.end = offset + len(read)

        out = read[offset % self.blocksize:offset % self.blocksize + length]
        have = len(out)
        if length < have:
            raise RuntimeError("Grabbed too much data")
        elif length == have:
            self.prefetch(offset)
            return out
        elif self.end and (offset + have) >= self.end:
            print(f"new_read at end.")
            return out
        else:
            return out + self.read(offset + have, length - have)

    def cache_read(self, offset, length):
        print(f"cache_read({offset}, {length})")

        block = self.block(offset)
        read = self.cache[block]
        self.hits[block] = time.monotonic()  # reward a cache hit.

        out = read[offset % self.blocksize:offset % self.blocksize + length]
        have = len(out)
        if length < have:
            raise RuntimeError("Grabbed too much data")
        elif length == have:
            self.prefetch(offset)
            return out
        elif self.end and (offset + have) >= self.end:
            print(f"cache_read at end.")
            return out
        else:
            print(f"cache_read (DEBUG) offset={offset}, have={have}, length={length}")
            return out + self.read(offset + have, length - have)
