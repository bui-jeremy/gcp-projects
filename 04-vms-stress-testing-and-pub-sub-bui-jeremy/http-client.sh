#!/bin/bash

num_clients=50

for i in $(seq 1 $num_clients); do
  python3 http-client.py --domain 104.197.59.40 --bucket jeremybui_ps2 --webdir files --num_requests 1000 --index 1000 --port 8080 --timeout 10 &
done

trap "kill 0" SIGINT

wait
