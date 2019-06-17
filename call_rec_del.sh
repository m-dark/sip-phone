#!/bin/sh
logfile=/etc/asterisk/script/log/call_rec_del.log
#dir=/var/spool/asterisk/monitor						#Каталог с файлами разговоров.
#dir=/dev/mapper/SangomaVG-root
date=`date +%Y.%m.%d' '%H:%M:%S`
#limit_size=70								#Лимит занятого места в процентах, после которого удаляются файлы.
dir=$1
limit_size=$2
if [[ "$dir" = dev/mapper/SangomaVG-root ]]; then
	dir_del=/var/spool/asterisk/monitor
else
	dir_del=$dir
fi
size=`df | grep $dir |  awk '{print $5}' | awk -F'%' '{print $1}'`
sizenul=`du -shm $dir_del | awk '{print $1}'`
echo $size
echo $dir_del
echo $sizenul
while [[ "$size" -ge "$limit_size" && "$sizenul" -gt 2000 ]]; do
	echo $date 'Диск загружен на: '$size'%' >> $logfile
	cd $dir_del
	dir_year=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`	#Находим самый старый каталог (сортировка по названию файла) год
	cd $dir_del/$dir_year
	dir_month=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`	#Находим самый старый каталог (сортировка по названию файла) месяц
	cd $dir_del/$dir_year/$dir_month
	dir_day=`(ls -lr | tail -n 1) | awk -F' ' '{print $9}'`		#Находим самый старый каталог (сортировка по названию файла) день
	file_del=`ls -l $dir_del/$dir_year/$dir_month/$dir_day`
		echo $date 'Удалили каталог '$dir_del/$dir_year/$dir_month/$dir_day >> $logfile
		echo $date 'C файлами ' $file_del >> $logfile
	rm -rf $dir_del/$dir_year/$dir_month/$dir_day			#Удаляем каталог со всеми файлами. один день записей.
	size=`df -l | grep $dir |  awk '{print $5}' | awk -F'%' '{print $1}'`
	date=`date +%Y.%m.%d' '%H:%M:%S`
	sizenul=`du -shm $dir_del | awk '{print $1}'`
done
exit 0
