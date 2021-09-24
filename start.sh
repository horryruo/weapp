#!/bin/bash



PORT="5001"



while [[ $(lsof -i:${PORT}|awk '{if(NR==2)print $2}') ]];do
echo "关闭占用端口程序pid： $(lsof -i:${PORT}|awk '{if(NR==2)print $2}')"
kill -9 $(lsof -i:${PORT}|awk '{if(NR==2)print $2}')
done

gunicorn -c gunicorn.conf.py --bind 0.0.0.0:"$PORT" apy:app --preload