#!/bin/bash

for file in logs/*_$1.log
do
  echo "=== Last line of $file ==="
  tail -n 1 "$file"
done
