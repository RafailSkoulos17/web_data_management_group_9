#!/bin/bash
for((i=0;i<8;i++))
do
   locust --locustfile locust_checkout.py --no-web  --slave --master-host=3.17.157.211  --logfile=checkout_log.log --csv=checkout &
done
