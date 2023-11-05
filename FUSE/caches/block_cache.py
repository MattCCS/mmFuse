
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


def start_background_load(buffer, offset, length, block, blocks, delay_seconds=0):
    t = threading.Thread(target=background_load, args=(buffer, offset, length, block, blocks, delay_seconds))
    t.start()


def background_load(buffer, offset, length, block, blocks, delay_seconds=0):
    time.sleep(delay_seconds)
    print(f"[r] Async read of block {block} ({offset=}), blocks {blocks} ({length=})")
    buffer.load_async(buffer.source(offset=offset, length=length), block, blocks)


class BlockwiseBuffer(AbstractBuffer):
    def __init__(self, source, size, blocksize=2_000_000, cache_limit=20, prefetch_blocks=2):
        super().__init__(source, cap=blocksize, end=size)
        self.blocksize = blocksize
        self.cache_limit = cache_limit
        self.prefetch_blocks = prefetch_blocks
        self.cache = {}
        self.stored = 0
        self.hits = {}
        self.requests = set()

    def load_async(self, bytez, start_block, blocks):
        print(f"[async receiving {start_block=}, {blocks=}]")
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
            if (next_block in self.cache) or (next_block in self.requests):
                continue

            blocks = 1  # NOTE(mcotton): We always request 1 block at a time.
            offset = next_block * self.blocksize
            length = blocks * self.blocksize

            if (self.end is not None):
                remaining = self.end - offset
                if remaining < 0:
                    continue
                length = min(length, remaining)

            print(f"(starting background load for: {next_block})")
            delay_seconds = (idx + 1) * 0.5
            start_background_load(
                buffer=self,
                offset=offset,
                length=length,
                block=next_block,
                blocks=blocks,
                delay_seconds=delay_seconds,
            )
            self.requests.add(next_block)

    def read(self, offset, length):
        print(self.hits)

        if offset < 0 or length < 0:
            raise RuntimeError("Offset and length can't be negative.")
        elif length == 0:
            out = b''

        self.prefetch(offset)

        block = self.block(offset)
        if block not in self.cache and block not in self.requests:
            out = self.new_read(offset, length)
        elif block in self.requests:
            print(f"[ ] Waiting for pending request...")
            for _ in range(5):
                time.sleep(0.1)
                if block in self.cache:
                    out = self.cache_read(offset, length)
            else:
                print(f"[!] Cache took too long to populate!")
                raise RuntimeError("cache delay")
        else:
            print(f"read (DEBUG) offset={offset}, length={length}")
            out = self.cache_read(offset, length)

        if self.cached_blocks() >= self.cache_limit:
            self.invalidate()

        return out

    def new_read(self, offset, length):
        print(f"new_read({offset}, {length})")

        block = self.block(offset)
        print(f"[r] Sync read of block {block}")
        if (self.end is not None):
            remaining = self.end - (block * self.blocksize)
            read = self.source(offset=block * self.blocksize, length=min(self.blocksize, remaining))
        else:
            read = self.source(offset=block * self.blocksize, length=self.blocksize)
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

        # TODO(mcotton): Consider this carefully.
        # if have <= length <= self.blocksize:
        #     print(f"cache_read empty block")
        #     # We have cached < blocksize, or even 0!
        #     # If they asked for something that would be encapsulated
        #     # in a single cache read, there's no reason to recurse or prefetch.
        #     return out
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
