#!/bin/bash
for((i=0;i<8;i++))
do
   locust --locustfile locust_stock.py --no-web  --slave --master-host=3.17.157.211 &
done
