#!/bin/bash

path="$(dirname "$(realpath "$0")")"
script="CPULogger.py"

echo PATH: $path
cd $path

echo Starting CPU Performance Logger Loop...

while true; do
  # Using +10 (low priority) so the logger never steals CPU time from the Estimators
  sudo nice -n 10 python3 $script
  sleep 1
done