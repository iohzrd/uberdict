#!/usr/bin/env bash

# tox doesn't behave well with pyenv, failing with error messages
# about python2.5 being unsupported even though we're not including
# the 2.5 env and python 2.5 isn't installed.
#
# This script clears any .pyenv directories from the PATH so they
# can't interfere, adds each python version's bin directory
# back to the PATH, then runs tox with the temporary PATH,
# passing through any args to tox.

set -o errexit

IFS=":"
tmp_path=""
for dirpath in $PATH; do
    if [[ ${dirpath} != */.pyenv/* ]]; then
        tmp_path="${tmp_path}:${dirpath}"
    fi
done

tmp_path="${tmp_path:1}"  # path without initial ':'
tox="$(PATH=${tmp_path} which tox)"

# add the python bin directories
for dirpath in $HOME/.pyenv/versions/*; do
    tmp_path="${tmp_path}:${dirpath}/bin"
done

PATH="${tmp_path}" exec $tox "$@"
