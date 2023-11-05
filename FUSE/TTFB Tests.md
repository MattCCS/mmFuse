Time-to-First-Byte Tests
========================

## New Requests
cat Media/.localized/en.strings  0.00s user 0.01s system 3% cpu 0.157 total
cat Media/.localized/ar.strings  0.00s user 0.01s system 3% cpu 0.170 total
cat Media/.localized/el.strings  0.00s user 0.01s system 3% cpu 0.155 total

## Cached Requests
cat Media/.localized/cs.strings  0.00s user 0.00s system 3% cpu 0.139 total
cat Media/.localized/cs.strings  0.00s user 0.01s system 21% cpu 0.034 total  # <--- cache is applied, far-side

cat Media/.localized/de.strings  0.00s user 0.01s system 5% cpu 0.127 total
cat Media/.localized/de.strings  0.00s user 0.00s system 18% cpu 0.021 total  # <--- cache is applied, far-side

## New Requests, with Redis
cat Media/.localized/en.strings  0.00s user 0.00s system 2% cpu 0.157 total
cat Media/.localized/ar.strings  0.00s user 0.00s system 4% cpu 0.061 total  # <--- Redis obviates need to read disk/decrypt data (after first run)
cat Media/.localized/el.strings  0.00s user 0.00s system 4% cpu 0.070 total

## New Requests, with Redis, and MM Session
cat Media/.localized/en.strings  0.00s user 0.00s system 4% cpu 0.064 total
cat Media/.localized/ar.strings  0.00s user 0.00s system 4% cpu 0.032 total
cat Media/.localized/el.strings  0.00s user 0.00s system 7% cpu 0.038 total
