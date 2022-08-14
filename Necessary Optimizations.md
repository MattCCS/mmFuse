# Necessary Optimizations

1. Cache MediaMan responses, prefetch data at the block level
    - iTunes/Music and other apps will frequently re-request the same blocks 2-4 times at once
    - Nearly x3 performance improvement of regular `cat`-ing of files
    - Vastly improved sequential reads, as `openssl` is invoked less frequently
    - Vastly improved Music.app latency, as that app performs rapid, tiny sequential reads

