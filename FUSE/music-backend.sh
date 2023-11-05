#!/bin/bash

mediaManPath="$HOME/home/code/mine/MediaMan"
latestMusicLibraryHash="xxh64:32ea82bd8e9d0a94"

. venv-rest2passthrough-mediaman/bin/activate
MMSRC=$mediaManPath ./rest2passthrough -i $latestMusicLibraryHash --service_selector="local"
