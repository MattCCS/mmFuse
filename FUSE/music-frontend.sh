#!/bin/bash

musicFolderPath="$HOME/home/music/Media"
fuseApiUrl="http://localhost:4001"

. venv-fuse2rest/bin/activate
./fuse2rest $musicFolderPath $fuseApiUrl --assume-static
