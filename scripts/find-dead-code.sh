#!/bin/bash

SAVED_PWD=$PWD

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

pushd "$DIR/.."

vulture FUSE --exclude FUSE/venv-fuse2rest,FUSE/venv-rest2passthrough-mediaman

popd
