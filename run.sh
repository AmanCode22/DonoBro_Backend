#!/bin/sh

PORT=8080
screen -S donorbro -X quit > /dev/null 2>&1

sleep 2







screen -dmS donorbro gunicorn -w 1 -k gevent --worker-connections 1000 --forwarded-allow-ips="*" -b 0.0.0.0:$PORT app:app

echo "SUCCESS: Server started on Port $PORT."
echo "View status with: screen -list"
