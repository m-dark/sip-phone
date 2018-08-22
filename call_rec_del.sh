#!/bin/sh
logfile=/etc/asterisk/script/log/call_rec_del.log
#dir=/var/spool/asterisk/monitor						#Каталог с файлами разговоров.
#dir=/dev/mapper/SangomaVG-root
dir=$1
date=`date +%Y.%m.%d' '%H:%M:%S`
#limit_size=70								#Лимит занятого места в процентах, после которого удаляются файлы.
limit_size=$2
size=`df | grep $dir |  awk '{print $5}' | awk -F'%' '{print $1}'`

while [ "$size" -ge "$limit_size" ]; do
	echo $date 'Диск загружен на: '$size'%' >> $logfile
	cd $dir
	dir_year=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`	#Находим самый старый каталог (сортировка по названию файла) год
	cd $dir/$dir_year
	dir_month=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`	#Находим самый старый каталог (сортировка по названию файла) месяц
	cd $dir/$dir_year/$dir_month
	dir_day=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`		#Находим самый старый каталог (сортировка по названию файла) день
	file_del=`ls -l $dir/$dir_year/$dir_month/$dir_day`
		echo $date 'Удалили каталог '$dir/$dir_year/$dir_month/$dir_day >> $logfile
		echo $date 'C файлами ' $file_del >> $logfile
	rm -rf $dir/$dir_year/$dir_month/$dir_day			#Удаляем каталог со всеми файлами. один день записей.
	size=`df -l | grep $dir |  awk '{print $5}' | awk -F'%' '{print $1}'`
	date=`date +%Y.%m.%d' '%H:%M:%S`
done
exit 0
