Performance vs OS
=================

Local SSD + net drive SSD.

Best times are taken to ignore things like drive sleep/wake.

File is: `('Chipmunks On 16 Speed - Sludgefest (Full Album)-TU-MYe0SL9Q.m4a', '54482274', 'xxh64:637ae521cb8da3d8', '07a52902-cf2a-4e47-9e96-4b1eadb2a402', [])`

54482274 bytes (54.48 MB)


OS Access
---------

### TTFB
time head -c 32 ~/home/MediaMan/07a52902-cf2a-4e47-9e96-4b1eadb2a402 >/dev/null
- 0.002 total
time head -c 32 /Volumes/Samsung_T3/MediaMan/5ab0bdc8-e963-440b-a4b0-92ca0fecbd43 >/dev/null
- 0.020 total

### Speed
time cat ~/home/MediaMan/07a52902-cf2a-4e47-9e96-4b1eadb2a402 >/dev/null
- 0.010 total (5,448 MB/s)
time cat /Volumes/Samsung_T3/MediaMan/5ab0bdc8-e963-440b-a4b0-92ca0fecbd43 >/dev/null
- 0.040 total (1,362 MB/s)


FUSE Access
-----------
(ignore the folder being named "movies")

### TTFB
time head -c 32 ~/home/movies/<random file> >/dev/null
- 0.014 total (preloaded + touched)
- 0.025 total (preloaded, not touched)
- 0.092 total (not preloaded)

### Speed
(files had to be chosen at random to avoid aggressive FUSE caching)
("CSP" = 4622359 bytes)

time cat ~/home/movies/Celestial\ Soda\ Pop.mp3 >/dev/null
- 0.084 total (55 MB/s)
time cat ~/home/movies/Celestial\ Soda\ Pop.mp3 >/dev/null
- 0.008 total (578 MB/s) (with FUSE + OS caching)


MM Access
---------

### TTFB
time mmd local streamrange xxh64:637ae521cb8da3d8 0 32 >/dev/null
- 0.150 total
time MM_USE_REDIS=1 mmd local streamrange xxh64:637ae521cb8da3d8 0 32 >/dev/null
- 0.120 total

time mmd sam streamrange xxh64:637ae521cb8da3d8 0 32 >/dev/null
- 0.200 total
time MM_USE_REDIS=1 mmd sam streamrange xxh64:637ae521cb8da3d8 0 32 >/dev/null
- 0.140 total

### Speed
time mmd local stream xxh64:637ae521cb8da3d8 >/dev/null
- 0.400 total (136 MB/s)
time MM_USE_REDIS=1 mmd local stream xxh64:637ae521cb8da3d8 >/dev/null
- 0.369 total (147 MB/s)

time mmd sam stream xxh64:637ae521cb8da3d8 >/dev/null
- 0.450 total (121 MB/s)
time MM_USE_REDIS=1 mmd sam stream xxh64:637ae521cb8da3d8 >/dev/null
- 0.386 total (141 MB/s)
