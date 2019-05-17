#!/bin/sh

if [ $3 = month ]; then
    start=`date +%Y.%m.%d' 00:00:00' -d"-1 month"`
    end=`date +%Y.%m.%d' 23:59:59'`
else
    start=`date +%Y.%m.%d' 00:00:00' -d"-1 day"`
    end=`date +%Y.%m.%d' 23:59:59' -d"-1 day"`
fi

/etc/asterisk/script/calls_in_out_all.py $start $end $1 $2
