Client-side Optimizations
=========================

## With HTTP Session, Caching, Block Prefetch, Redis, MM Session
01 One More Time.m4a                     10602424 / 0.297 total = 34.04 MB/s
02 Aerodynamic.m4a                        7153453 / 0.174 total = 39.21 MB/s
03 Digital Love.m4a                      10793234 / 0.297 total = 34.66 MB/s
04 Harder, Better, Faster, Stronger.m4a   7846586 / 0.175 total = 42.76 MB/s
05 Crescendolls.m4a                       7705917 / 0.181 total = 40.60 MB/s
06 Nightvision.m4a                        3517255 / 0.153 total = 21.92 MB/s
07 Superheroes.m4a                        8199525 / 0.284 total = 27.53 MB/s
08 High Life.m4a                          7289549 / 0.177 total = 39.28 MB/s
09 Something About Us.m4a                 8183018 / 0.284 total = 27.48 MB/s
10 Voyager.m4a                            8305478 / 0.297 total = 26.67 MB/s
11 Veridis Quo.m4a                       11309368 / 0.289 total = 37.32 MB/s
12 Short Circuit.m4a                      6440145 / 0.174 total = 35.30 MB/s
13 Face To Face.m4a                       8571383 / 0.290 total = 28.19 MB/s
14 Too Long.m4a                          22440743 / 0.537 total = 39.85 MB/s
One More Time (extended radio edit).mp3   5887713 / 0.169 total = 33.22 MB/s

## With HTTP Session, Caching, Block Prefetch, Redis (between sessions)
01 One More Time.m4a                     10602424 / 0.333 total = 30.36 MB/s
02 Aerodynamic.m4a                        7153453 / 0.285 total = 23.94 MB/s
03 Digital Love.m4a                      10793234 / 0.365 total = 28.20 MB/s
04 Harder, Better, Faster, Stronger.m4a   7846586 / 0.210 total = 35.63 MB/s
05 Crescendolls.m4a                       7705917 / 0.245 total = 30.00 MB/s
06 Nightvision.m4a                        3517255 / 0.211 total = 15.90 MB/s
07 Superheroes.m4a                        8199525 / 0.334 total = 23.41 MB/s
08 High Life.m4a                          7289549 / 0.226 total = 30.76 MB/s
09 Something About Us.m4a                 8183018 / 0.324 total = 24.09 MB/s
10 Voyager.m4a                            8305478 / 0.327 total = 24.22 MB/s
11 Veridis Quo.m4a                       11309368 / 0.317 total = 34.02 MB/s
12 Short Circuit.m4a                      6440145 / 0.224 total = 27.42 MB/s
13 Face To Face.m4a                       8571383 / 0.320 total = 25.54 MB/s
14 Too Long.m4a                          22440743 / 0.591 total = 36.21 MB/s
One More Time (extended radio edit).mp3   5887713 / 0.225 total = 24.96 MB/s

## With HTTP Session, Caching, Block Prefetch
01 One More Time.m4a                     10602424 / 0.614 total = 17.27 MB/s
02 Aerodynamic.m4a                        7153453 / 0.385 total = 18.58 MB/s
03 Digital Love.m4a                      10793234 / 0.641 total = 16.84 MB/s
04 Harder, Better, Faster, Stronger.m4a   7846586 / 0.386 total = 20.33 MB/s
05 Crescendolls.m4a                       7705917 / 0.438 total = 17.59 MB/s
06 Nightvision.m4a                        3517255 / 0.420 total =  8.37 MB/s
07 Superheroes.m4a                        8199525 / 0.535 total = 15.33 MB/s
08 High Life.m4a                          7289549 / 0.349 total = 20.89 MB/s
09 Something About Us.m4a                 8183018 / 0.652 total = 12.55 MB/s
10 Voyager.m4a                            8305478 / 0.554 total = 14.99 MB/s
11 Veridis Quo.m4a                       11309368 / 0.554 total = 20.41 MB/s
12 Short Circuit.m4a                      6440145 / 0.375 total = 17.17 MB/s
13 Face To Face.m4a                       8571383 / 0.650 total = 13.19 MB/s
14 Too Long.m4a                          22440743 / 0.997 total = 22.51 MB/s
One More Time (extended radio edit).mp3   5887713 / 0.372 total = 15.83 MB/s

## With HTTP Session
8709719 / 1.100s = 7.92 MB/s
7708498 / 1.125s = 6.85 MB/s
5249629 / 0.789s = 6.65 MB/s
7343000 / 1.082s = 6.79 MB/s

## Without HTTP Session
8709719 / 1.395s = 6.24 MB/s
6981889 / 1.172s = 5.96 MB/s
5249629 / 0.940s = 5.58 MB/s


MMBackend-Side Optimizations
============================
## Using block-level caching on decrypted responses from MediaMan
(Get stats on this.)

## 


FUSE-side Optimizations
=======================

## Caching Non-Data Responses (--assume-static)
ls -G Media  0.00s user 0.00s system 2% cpu 0.245 total  # <--- first load is slow
ls -G Media  0.00s user 0.00s system 2% cpu 0.028 total
ls -G Media  0.00s user 0.00s system 2% cpu 0.025 total

### Test: Clearing Both Caches
ls -G Media  0.00s user 0.01s system 3% cpu 0.239 total

- No different than first-load with cache
- Means the network call is order-of-magnitude slower than all other concerns

## Without Caching
ls -G Media  0.00s user 0.00s system 2% cpu 0.244 total
ls -G Media  0.00s user 0.00s system 2% cpu 0.299 total
ls -G Media  0.00s user 0.00s system 2% cpu 0.256 total
