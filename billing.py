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
direction = set(['all','city','810','710','610','89','79','69','8_rf','7_rf','6_rf'])
trunk = set(['all'])
extension_ok = 0
direction_ok = 0
trunk_ok = 0

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
#print(trunk)
#print(extension)

asteriskcdrdb = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
cursor = asteriskcdrdb.cursor()

##python3.6 billing.py 2019.01.01 00:00:00 2019.03.07 23:00:00 all(trunk) all(direction) all(number)
cursor.execute("SELECT calldate, cnum, lastdata, billsec FROM cdr WHERE calldate BETWEEN (%s' '%s) AND (%s' '%s) AND (LENGTH(cnum) < 4) AND (LENGTH(dst) > 3) AND (dst != 'hangup') AND (billsec != '0')", (array[1], array[2], array[3], array[4]))
#               "SELECT calldate, cnum, lastdata, billsec from cdr WHERE (calldate between '2019-03-01 00:00:00' and '2019-03-06 09:59:59') and (LENGTH(cnum) < 4) and (LENGTH(dst) > 3) and (dst != 'hangup') and (billsec != '0');
for row in cursor:
	if array[5] == 'all':
		print(row)
#	else:
#		print('sdsds')

cursor.close()
asteriskcdrdb.close()


'''
one = 0
uniqueid = 0
time_start = 0
time_end  = 0
number_in = 0
number_out = 0
dictionary = {}
for row in cursor:
	if row[3]!='':
		if one == 0:
			one = 1
			uniqueid = row[2]
			time_start = datetime.timestamp(row[0])
			time_end = time_start + row[1]
			number_in = row[3]
#			print(str(time_start)+' '+str(time_end)+' '+str(number_in))
		else:
			if uniqueid == row[2]:
				if time_end < int(datetime.timestamp(row[0])) + int(row[1]):
					time_end = int(datetime.timestamp(row[0])) + int(row[1])
			else:
###				print('-> '+str(int(time_start))+' '+str(int(time_end))+' '+str(number_in))
				# Заносим данные в ассоциативный массив входящие вызовы и all
				i = int(time_start)
				while i <= int(time_end):
					if number_in not in dictionary:
						dictionary[number_in] = {}
					if i not in dictionary[number_in]:
						dictionary[number_in][i] = {'in':1, 'out':0, 'all':1}
					else:
						dictionary[number_in][i]['in'] = dictionary[number_in][i]['in'] + 1
						dictionary[number_in][i]['all'] = dictionary[number_in][i]['all'] + 1
					i += 1
				uniqueid = row[2]
				time_start = datetime.timestamp(row[0])
				time_end = time_start + row[1]
				number_in = row[3]
#				tdate = datetime.timestamp(row[0])
#				print (str(row[0])+"\t"+str(row[1])+"\t"+str(datetime.fromtimestamp(float(row[2])))+"\t"+str(row[3])+"\t"+str(row[4]))
	else:
###		print ('<- '+str(int(datetime.timestamp(row[0])))+"\t"+str(int(datetime.timestamp(row[0])) + row[1])+"\t"+str(row[4]))
		number_out = row[4]
		j = int(datetime.timestamp(row[0]))
		while j <= datetime.timestamp(row[0]) + row[1]:
			if number_out not in dictionary:
				dictionary[number_out] = {}
			if j not in dictionary[number_out]:
				dictionary[number_out][j] = {'in':0, 'out':1, 'all':1}
			else:
				dictionary[number_out][j]['out'] = dictionary[number_out][j]['out'] + 1
				dictionary[number_out][j]['all'] = dictionary[number_out][j]['all'] + 1
			j += 1
###print('-> '+str(int(time_start))+' '+str(int(time_end))+' '+str(number_in))

i = int(time_start)
while i <= int(time_end):
	if number_in not in dictionary:
		dictionary[number_in] = {}
	if i not in dictionary[number_in]:
		dictionary[number_in][i] = {'in':1, 'out':0, 'all':1}
	else:
		dictionary[number_in][i]['in'] = dictionary[number_in][i]['in'] + 1
		dictionary[number_in][i]['all'] = dictionary[number_in][i]['all'] + 1
	i += 1
cursor.close()
asteriskcdrdb.close()

print('Number Date time  in  out all')
dict_number = {'3573079':2, '3573097':37, '3856610':10, '3857018':2, '3857320':2, '3857500':3, '3857710':3, '3857750':4, '3857787':3, '3857900':22, '3857901':2, '3858068':4, '3858088':4, '3859101':2, '3573011':2}
for key_number in sorted(dictionary.keys()):
	time_old = 0
	calls_in = 0
	calls_out = 0
	calls_all = 0
	print_call = 0
#	print(key_number)
	for key_date in sorted(dictionary[key_number].keys()):
		if time_old == 0:
			if dictionary[key_number][key_date]['all'] > 1:
				print(str(key_number)+"\t"+str(datetime.fromtimestamp(key_date))+" - ",end = '')
				print_call = 1
		else:
			if((calls_in == dictionary[key_number][key_date]['in'] == 0) and (calls_out == dictionary[key_number][key_date]['out'] == 0) and (calls_all == dictionary[key_number][key_date]['all'] == 0)):
				calls_tmp = 0
			elif(((time_old + 1) != key_date) or (calls_in != dictionary[key_number][key_date]['in']) or (calls_out != dictionary[key_number][key_date]['out']) or (calls_all != dictionary[key_number][key_date]['all'])):
				if print_call == 1 and calls_all > 1:
					print(str(datetime.fromtimestamp(time_old))+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))
					print_call = 0
#				if dictionary[key_number][key_date]['all'] >= 1:
#					print(str(datetime.fromtimestamp(key_date))+" - ",end = '')
				if key_number in dict_number:
					if dictionary[key_number][key_date]['all'] >= dict_number[key_number]:
						print(str(key_number)+"\t"+str(datetime.fromtimestamp(key_date))+" - ",end = '')
#						print(str(key_number+"\t"+str(datetime.fromtimestamp(key_date))+"\t"+str(dictionary[key_number][key_date]['in'])+"\t"+str(dictionary[key_number][key_date]['out'])+"\t"+str(dictionary[key_number][key_date]['all'])))
						print_call = 1
				else:
					if dictionary[key_number][key_date]['all'] > 1:
#						print('!!!!!'+str(key_number+"\t"+str(datetime.fromtimestamp(key_date))+"\t"+str(dictionary[key_number][key_date]['in'])+"\t"+str(dictionary[key_number][key_date]['out'])+"\t"+str(dictionary[key_number][key_date]['all'])))
						print('!'+str(key_number)+"\t"+str(datetime.fromtimestamp(key_date))+" - ",end = '')
						print_call = 1
		time_old = key_date
		calls_in = dictionary[key_number][key_date]['in']
		calls_out = dictionary[key_number][key_date]['out']
		calls_all = dictionary[key_number][key_date]['all']
	if print_call == 1:
		print(str(datetime.fromtimestamp(key_date))+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))
print('Date time  in  out all')
dict_all = {}
#{'in': 0,'out': 0,'all':0}
for key_number in sorted(dictionary.keys()):
#	print(key_number)
	for key_date in sorted(dictionary[key_number].keys()):
		if key_date not in dict_all:
			dict_all[key_date] = {'in':0, 'out':0, 'all':0}
##		print("\t"+str(key_date)+"\t"+str(dictionary[key_number][key_date]))
		dict_all[key_date]['in'] = int(dict_all[key_date]['in']) + int(dictionary[key_number][key_date]['in'])
		dict_all[key_date]['out'] = int(dict_all[key_date]['out']) + int(dictionary[key_number][key_date]['out'])
		dict_all[key_date]['all'] = int(dict_all[key_date]['all']) + int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])
#print('-> '+key_number+"\t"+str(key_date)+"\t"+str(dictionary[key_number][key_date]['in']))

time_old = 0
calls_in = 0
calls_out = 0
calls_all = 0
print_call = 0
for key_all in sorted(dict_all.keys()):
	if time_old == 0:
#		print(str(datetime.fromtimestamp(key_all))+"\t"+str(dict_all[key_all]['in'])+"\t"+str(dict_all[key_all]['out'])+"\t"+str(dict_all[key_all]['all'])+"\t-\t",end = '')
		print(str(datetime.fromtimestamp(key_all))+" - ",end = '')
		print_call = 1
	else:
		if((calls_in == dict_all[key_all]['in'] == 0) and (calls_out == dict_all[key_all]['out'] == 0) and (calls_all == dict_all[key_all]['all'] == 0)):
			calls_tmp = 0
		elif(((time_old + 1) != key_all) or (calls_in != dict_all[key_all]['in']) or (calls_out != dict_all[key_all]['out']) or (calls_all != dict_all[key_all]['all'])):
			if print_call == 1:
				print(str(datetime.fromtimestamp(time_old))+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))
				print_call = 0
#			print(str(datetime.fromtimestamp(key_all))+"\t"+str(dict_all[key_all]['in'])+"\t"+str(dict_all[key_all]['out'])+"\t"+str(dict_all[key_all]['all'])+"\t-\t",end = '')
			if dict_all[key_all]['all'] >= 5:
				print(str(datetime.fromtimestamp(key_all))+" - ",end = '')
				print_call = 1
#		else:
#			print('Error!',end='')
	time_old = key_all
	calls_in = dict_all[key_all]['in']
	calls_out = dict_all[key_all]['out']
	calls_all = dict_all[key_all]['all']
print(str(datetime.fromtimestamp(key_all))+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))

'''