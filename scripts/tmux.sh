#!/usr/bin/env bash

set -eu

PROJDIR="$(readlink -m -n $(dirname ${BASH_SOURCE[0]})/..)"

tmux new-session -s udict -n tests -d
tmux send-keys -t udict "cd $PROJDIR; py.test --color=yes -f" C-m
tmux send-keys -t udict "cd $PROJDIR" C-m
tmux split-window -v -t udict
tmux attach-session -t udict
