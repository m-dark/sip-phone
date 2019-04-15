#!/usr/bin/env python3.6

import os
import subprocess
import pymysql
import sys
import re
#sys.setdefaultencoding('utf-8')
from datetime import datetime
#date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
array = []
extension = set(['all'])
direction = set(['all','city','810','710','610','89','79','69','8','7','6','77','10'])
trunk = set(['all'])
tarif = dict()
info_extension_price = dict()
info_extension_price_p = dict()
info_all_extension =  dict()
info_all_extension_price =  dict()
extension_counter = dict()
extension_minutes = dict()
extension_price = dict()
extension_ok = 0
direction_ok = 0
trunk_ok = 0

def direction_function(date_time, extension_number, trunk, number_to, call_duration, stat_duration_extension, *direction_fun):
	direction_fun_iy='Error'
	minutes=int()
	prefix_direction_yes=0
	minutes_and_sec=divmod(call_duration,60)
	if minutes_and_sec[1] > 0:
		minutes=minutes_and_sec[0]+1
	else:
		minutes=minutes_and_sec[0]
	result_number_to=re.match(r"^\d{6,7}$", number_to)
	if result_number_to is not None:
		number_to='city'+number_to
	number_prefix_end=str()
	for direction_fun_i in direction_fun:
		number_prefix=number_to
		while len(number_prefix)>=1 and prefix_direction_yes==0:
			if tarif[trunk][str(direction_fun_i)].get(number_prefix) is not None:
#				print(number_prefix)
				prefix_direction_yes=1
				direction_fun_iy=direction_fun_i
				number_prefix_end=number_prefix
				break
			number_prefix=number_prefix[:-1]

	if prefix_direction_yes!=0:
		if info_extension_price.get(trunk) is None:
			info_extension_price[trunk]={}
			info_extension_price_p[trunk]={}
		if info_extension_price[trunk].get(direction_fun_iy) is None:
			info_extension_price[trunk][direction_fun_iy]={}
			info_extension_price_p[trunk][direction_fun_iy]={}
		if info_extension_price[trunk][direction_fun_iy].get(number_prefix_end) is None:
			info_extension_price[trunk][direction_fun_iy][number_prefix_end]={}
			info_extension_price[trunk][direction_fun_iy][number_prefix_end]['counter']=int()
			info_extension_price[trunk][direction_fun_iy][number_prefix_end]['city']=str()
			info_extension_price[trunk][direction_fun_iy][number_prefix_end]['minut']=int()
			info_extension_price[trunk][direction_fun_iy][number_prefix_end]['price']=float()
			info_extension_price_p[trunk][direction_fun_iy][number_prefix_end]=float()
		info_extension_price[trunk][direction_fun_iy][number_prefix_end]['counter']+=1
		info_extension_price[trunk][direction_fun_iy][number_prefix_end]['city']=tarif[trunk][direction_fun_iy][number_prefix_end]['city']+' ('+tarif[trunk][direction_fun_iy][number_prefix_end]['region']+')'
		info_extension_price[trunk][direction_fun_iy][number_prefix_end]['minut']+=minutes
		info_extension_price[trunk][direction_fun_iy][number_prefix_end]['price']+=int(minutes)*float(str(tarif[trunk][direction_fun_iy][number_prefix_end]['price']).replace(',' ,'.'))
		info_extension_price_p[trunk][direction_fun_iy][number_prefix_end]+=int(minutes)*float(str(tarif[trunk][direction_fun_iy][number_prefix_end]['price']).replace(',' ,'.'))

		if info_all_extension.get(trunk) is None:
			info_all_extension[trunk]={}
			info_all_extension_price[trunk]={}
		if info_all_extension[trunk].get(direction_fun_iy) is None:
			info_all_extension[trunk][direction_fun_iy]={}
			info_all_extension_price[trunk][direction_fun_iy]={}
		if info_all_extension[trunk][direction_fun_iy].get(number_prefix_end) is None:
			info_all_extension[trunk][direction_fun_iy][number_prefix_end]={}
			info_all_extension_price[trunk][direction_fun_iy][number_prefix_end]={}

		if stat_duration_extension=='all' or stat_duration_extension==number_prefix_end:
			if info_all_extension[trunk][direction_fun_iy][number_prefix_end].get(extension_number) is None:
				info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]={}
				info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['counter']=int()
				info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['minut']=int()
				info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['price']=float()
				info_all_extension_price[trunk][direction_fun_iy][number_prefix_end][extension_number]=float()
			info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['counter']+=1
			info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['minut']+=minutes
			info_all_extension[trunk][direction_fun_iy][number_prefix_end][extension_number]['price']+=int(minutes)*float(str(tarif[trunk][direction_fun_iy][number_prefix_end]['price']).replace(',' ,'.'))
			info_all_extension_price[trunk][direction_fun_iy][number_prefix_end][extension_number]+=int(minutes)*float(str(tarif[trunk][direction_fun_iy][number_prefix_end]['price']).replace(',' ,'.'))

		if extension_counter.get(extension_number) is None:
			extension_counter[extension_number]=int()
			extension_minutes[extension_number]=int()
			extension_price[extension_number]=float()
		extension_counter[extension_number]+=1
		extension_minutes[extension_number]+=int(minutes)
		extension_price[extension_number]+=int(minutes)*float(str(tarif[trunk][direction_fun_iy][number_prefix_end]['price']).replace(',' ,'.'))
##	else:
##		print('Error_09: Нет префикса для номера '+number_to+' в файлах с тарифами '+str(dir_trunk)+'/'+trunk+'/')

for param in sys.argv:
	array.append(param)
#result=re.match(r'((\d+(-\d+)*),\d\,\d+\,\d+)', row[1])
result_date_start=re.match(r'(\d\d\d\d\.\d\d.\d\d)', array[1])
if result_date_start is None:
	print('У даты начала не корректный формат (2017.01.01)!')
	sys.exit()
result_time_start=re.match(r'(\d\d\:\d\d:\d\d)', array[2])
if result_time_start is None:
	print('Время начала имеет не корректный формат (00:00:00)!')
	sys.exit()
result_date_end=re.match(r'(\d\d\d\d\.\d\d.\d\d)', array[3])
if result_date_end is None:
	print('У конечной даты не корректный формат (2039.01.31)!')
	sys.exit()
result_time_end=re.match(r'(\d\d\:\d\d:\d\d)', array[4])
if result_time_end is None:
	print('Конечное время имеет не корректный формат (23:59:59)!')
	sys.exit()

asteriskdb = pymysql.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor_trunk = asteriskdb.cursor()
cursor_trunk.execute("SELECT channelid FROM trunks")
if cursor_trunk!='':
	for row_trunks in cursor_trunk:
		trunk.add(row_trunks[0])
else:
	print('Error_01: Транки отсутствуют на сервере!')
cursor_trunk.close()

cursor_extension = asteriskdb.cursor()
cursor_extension.execute("SELECT extension FROM users")
if cursor_extension!='':
	for row_extension in cursor_extension:
		extension.add(row_extension[0])
else:
	print('Error_02: Внутренние номера отсутствуют на сервере!')
cursor_extension.close()
asteriskdb.close()

for row_extension in extension:
	if row_extension == array[5]:
		extension_ok = 1
		break
if extension_ok == 0:
	print('Нет такого номера на сервере!')
	print('Возможные варианты:'+str(extension))
	sys.exit()
for row_direction in direction:
	if row_direction == array[6]:
		direction_ok = 1
		break
if direction_ok == 0:
	print('Нет такого направления!')
	print('Возможные варианты:'+str(direction))
	sys.exit()
for row_trunk in trunk:
	if row_trunk == array[7]:
		trunk_ok = 1
		break
if trunk_ok == 0:
	print('Нет такого транка на сервере!')
	print('Возможные варианты:'+str(trunk))
	sys.exit()

array_trunk = []
dir_trunk = '/etc/asterisk/script/billing'
if array[7]=='all':
	for tr in trunk:
		if tr != 'all':
			array_trunk.append(tr)
else:
	array_trunk.append(array[7])

for dir_tr in array_trunk:
	tarif[dir_tr]={}
	print(dir_tr)
	tree = os.walk(dir_trunk+'/'+dir_tr)
	for i in tree:
		xz=i[2]
		for file_i in range(len(xz)):
#			print(xz[file_i])
			file_open = open (str(dir_trunk)+'/'+str(dir_tr)+'/'+xz[file_i],'r')
			direction_tarif=xz[file_i].split('.')
			tarif[dir_tr][direction_tarif[0]]={}
			for line in (line.rstrip() for line in file_open.readlines()):
				result_line=re.match(r"^\d{1,11}\;([ \-\.А-Яа-яA-Za-z0-9])+\;([ \-А-Яа-яA-Za-z])+\;((\d+\,\d+)|\d+)", line)
				if result_line is not None:
					prefix_number=line.split(';')
					if tarif[dir_tr][direction_tarif[0]].get(direction_tarif[0]+prefix_number[0]) is None:
						tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]={}
						tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]['counter']=int()
					tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]['counter']+=1
					tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]['city']=prefix_number[1]
					tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]['region']=prefix_number[2]
					tarif[dir_tr][direction_tarif[0]][direction_tarif[0]+prefix_number[0]]['price']=prefix_number[3]
				else:
					print('Error_05: В строке '+"\t"+line+' файла '+"\t"+str(dir_trunk)+'/'+str(dir_tr)+'/'+xz[file_i]+' ошибка!')
					sys.exit()
			file_open.close()
mayak=0
array_direction_all=[]
for key_trunk in tarif:
	if ((array[6] != 'all' and array[7] != 'all') and (tarif[key_trunk].get(array[6]) is None)):
		mayak=1
		print('Error_08: Нет файла с тарифами для направления '+array[6]+' в каталоге '+str(dir_trunk)+'/'+str(dir_tr)+', есть только для направлений: ')
	for key_direction in tarif[key_trunk]:
		if mayak==1:
			print(key_direction)
		array_direction_all.append(key_direction)
		for key_prefix in tarif[key_trunk][key_direction]:
			if tarif[key_trunk][key_direction][key_prefix]['counter'] > 1:
				print('Error_06: Для транка '+str(key_trunk)+' и направления '+str(key_direction)+' префикс '+str(key_prefix)+' прописан '+str(tarif[key_trunk][key_direction][key_prefix]['counter'])+' раз(а)!')
#sys.exit()

asteriskcdrdb = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
cursor = asteriskcdrdb.cursor()
if array[5]=='all':
	cursor.execute("SELECT calldate, cnum, lastdata, billsec FROM cdr WHERE calldate BETWEEN (%s' '%s) AND (%s' '%s) AND (LENGTH(cnum) < 4) AND (LENGTH(dst) > 4) AND (dst != 'hangup') AND (billsec != '0') AND (lastdata != '')", (array[1], array[2], array[3], array[4]))
else:
	cursor.execute("SELECT calldate, cnum, lastdata, billsec FROM cdr WHERE calldate BETWEEN (%s' '%s) AND (%s' '%s) AND (LENGTH(cnum) < 4) AND (LENGTH(dst) > 4) AND (dst != 'hangup') AND (billsec != '0') AND (lastdata != '') AND (cnum = %s)", (array[1], array[2], array[3], array[4], array[5]))
##python3.6 billing.py 2019.01.01 00:00:00 2019.03.07 23:00:00 all(trunk) all(direction) all(number)
##cursor.execute("SELECT calldate, cnum, lastdata, billsec FROM cdr WHERE calldate BETWEEN (%s' '%s) AND (%s' '%s) AND (LENGTH(cnum) < 4) AND (LENGTH(dst) > 3) AND (dst != 'hangup') AND (billsec != '0')", (array[1], array[2], array[3], array[4]))
#               "SELECT calldate, cnum, lastdata, billsec from cdr WHERE (calldate between '2019-03-01 00:00:00' and '2019-03-06 09:59:59') and (LENGTH(cnum) < 4) and (LENGTH(dst) > 3) and (dst != 'hangup') and (billsec != '0');
for row in cursor:
	if re.match(r'PJSIP/', row[2]) is not None:
		trunk_name=row[2].split('/')
		trunk_name_1=trunk_name[1].split('@')
		trunk_name_2=trunk_name_1[1].split(',')
		trunk_finite=trunk_name_2[0]
		number_to=trunk_name_1[0]
	elif re.match(r'SIP', row[2]) is not None:
		trunk_name=row[2].split('/')
		trunk_finite=trunk_name[1]
		number_to=trunk_name[2].split(',')[0]
	else:
		print('Error_04: '+str(row)+' Не понятно что за транк!')
		continue
	if array[7]!='all' and array[7]==trunk_finite:
		if array[6]!='all':
			array_direction_all=[]
			array_direction_all.append(array[6])
		direction_function(row[0],row[1],trunk_finite,number_to,row[3],array[8],*array_direction_all)
#		print(str(row[0])+' '+str(row[1])+' '+trunk_finite+' '+number_to+' '+str(row[3]))
	elif array[7]=='all':
		if array[6]!='all':
			array_direction_all=[]
			array_direction_all.append(array[6])
		direction_function(row[0],row[1],trunk_finite,number_to,row[3],array[8],*array_direction_all)
#		print(str(row[0])+' '+str(row[1])+' '+trunk_finite+' '+number_to+' '+str(row[3]))

cursor.close()
asteriskcdrdb.close()

for key_trunk in info_extension_price_p:
	print("\n"+'========================================================================================'+"\n"+'Транк: '+key_trunk)
	for key_direction in info_extension_price_p[key_trunk]:
		print('========================================================================================'+"\n"+'Направление: '+key_direction+"\n"+'----------------------------------------------------------------------------------------')
		for key_pref in sorted(info_extension_price_p[key_trunk][key_direction].items(), key=lambda x:x[1], reverse=True):
			print("%-11s %-50s %-8s %-10s %-10s" % (key_pref[0],str(info_extension_price[key_trunk][key_direction][key_pref[0]]['city']),str(info_extension_price[key_trunk][key_direction][key_pref[0]]['counter']),str(info_extension_price[key_trunk][key_direction][key_pref[0]]['minut']),str(round(key_pref[1], 1))))
			if info_all_extension_price[key_trunk][key_direction].get(key_pref[0]) is not None:
				for key_extension_number in sorted(info_all_extension_price[key_trunk][key_direction][str(key_pref[0])].items(), key=lambda x:x[1], reverse=True):
					print("%-4s %-55s %-8s %-10s %-10s" % ('    |_',key_extension_number[0],str(info_all_extension[key_trunk][key_direction][key_pref[0]][key_extension_number[0]]['counter']),str(info_all_extension[key_trunk][key_direction][key_pref[0]][key_extension_number[0]]['minut']),str(round(key_extension_number[1], 1))))
			else:
				continue
print("\n"+'===================================================================')
print('|Номер | Попыток| Минут    | Рублей|')
print('-----------------------------------')
for number_price in sorted(extension_price.items(), key=lambda x:x[1], reverse=True):
	print("%-8s %-8s %-10s %-10s" % (str(number_price[0]),extension_counter[number_price[0]],extension_minutes[number_price[0]],str(round(number_price[1]))))
print("\n"+'===================================================================')
