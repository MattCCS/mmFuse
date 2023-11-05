#!/bin/bash

moviesFolderPath="$HOME/home/movies"
fuseApiUrl="http://localhost:4001"

. venv-fuse2rest/bin/activate
./fuse2rest $moviesFolderPath $fuseApiUrl --assume-static
