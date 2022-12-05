#!/bin/sh

year=`date +%Y -d"-1 day"`
month=`date +%m -d"-1 day"`
day=`date +%d -d"-1 day"`

if [ -d "/mnt/records/${year}" ]; then
    echo
else
    mkdir "/mnt/records/${year}"
fi

if [ -d "/mnt/records/${year}/${month}" ]; then
    echo
else
    mkdir "/mnt/records/${year}/${month}"
fi

dir_monitor=/var/spool/asterisk/monitor/${year}/${month}/${day}
dir_sb=/mnt/records/${year}/${month}

rsync -rptgo --bwlimit=5000 --delete --delete-after ${dir_monitor} ${dir_sb}
