#!/usr/bin/env python3.6

import os
import subprocess
import pymysql
import sys
import re
from datetime import datetime
#date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
array = []
dict_number = {}
dir_conf = '/etc/asterisk/script/';
freepbx_pass = open (str(dir_conf)+'freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	result_line=re.match(r'dict_number = ', line)
	if result_line is not None:
		param_fixedcid=line.split(' = ')
		dict_number_array=param_fixedcid[1].split(',')
		for num_lin in dict_number_array:
			number_line=num_lin.split(':')
			dict_number[str(number_line[0])]=int(number_line[1])
freepbx_pass.close()

for param in sys.argv:
	array.append(param)
db = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT calldate, duration, uniqueid, did, outbound_cnum FROM cdr WHERE calldate BETWEEN (%s' '%s) AND (%s' '%s) AND (did!='' OR outbound_cnum!='') ORDER BY uniqueid", (array[1], array[2], array[3], array[4]))
#cursor.execute("SELECT calldate, duration, uniqueid, did, outbound_cnum FROM cdr WHERE calldate BETWEEN '2018-11-07 14:00:00' AND '2018-11-07 14:10:00' AND (did!='' OR outbound_cnum!='') ORDER BY uniqueid")
#row[0]=calldate
#row[1]=duration
#row[2]=uniqueid
#row[3]=did
#row[4]=outbound_cnum

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
db.close()
print('____________________________________________________________________________________')
print('|       |         |                      |               |                 |        | ')
print('| Номер |  Дата   |  Временной период    |   Входящие    |   Исходящие     |   Все  |')
#dict_number = {'3573079':2, '3573097':37, '3856610':10, '3857018':2, '3857320':2, '3857500':3, '3857710':3, '3857750':4, '3857787':3, '3857900':22, '3857901':2, '3858068':4, '3858088':4, '3859101':2, '3573011':2}
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
				print(str(key_number)+' '+str(datetime.fromtimestamp(key_date))+" - ",end = '')
				print_call = 1
		else:
			if((calls_in == dictionary[key_number][key_date]['in'] == 0) and (calls_out == dictionary[key_number][key_date]['out'] == 0) and (calls_all == dictionary[key_number][key_date]['all'] == 0)):
				calls_tmp = 0
			elif(((time_old + 1) != key_date) or (calls_in != dictionary[key_number][key_date]['in']) or (calls_out != dictionary[key_number][key_date]['out']) or (calls_all != dictionary[key_number][key_date]['all'])):
				if print_call == 1 and calls_all > 1:
					only_time = str(datetime.fromtimestamp(time_old)).split(' ')
					print(only_time[1]+"\t\t"+str(calls_in)+"\t\t"+str(calls_out)+"\t\t"+str(calls_all))
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
						print('!'+str(key_number)+' '+str(datetime.fromtimestamp(key_date))+" - ",end = '')
						print_call = 1
		time_old = key_date
		calls_in = dictionary[key_number][key_date]['in']
		calls_out = dictionary[key_number][key_date]['out']
		calls_all = dictionary[key_number][key_date]['all']
	if print_call == 1:
		only_time = str(datetime.fromtimestamp(key_date)).split(' ')
		print(only_time[1]+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))
print('____________________________________________________________________________')
print('|         |                      |               |                 |        | ')
print('|  Дата   |  Временной период    |   Входящие    |   Исходящие     |   Все  |')
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
dtae_new = '1970.01.01'
start_yes = 0
for key_all in sorted(dict_all.keys()):
#	if time_old == 0:
#		print(str(datetime.fromtimestamp(key_all))+"\t"+str(dict_all[key_all]['in'])+"\t"+str(dict_all[key_all]['out'])+"\t"+str(dict_all[key_all]['all'])+"\t-\t",end = '')
#		print('|_________|______________________|_______________|_________________|_________|')
#		print(str(datetime.fromtimestamp(key_all))+" - ",end = '')
#		print_call = 1
#	else:
	if time_old != 0:
		if((calls_in == dict_all[key_all]['in'] == 0) and (calls_out == dict_all[key_all]['out'] == 0) and (calls_all == dict_all[key_all]['all'] == 0)):
			calls_tmp = 0
		elif(((time_old + 1) != key_all) or (calls_in != dict_all[key_all]['in']) or (calls_out != dict_all[key_all]['out']) or (calls_all != dict_all[key_all]['all'])):
			if print_call == 1:
				only_time = str(datetime.fromtimestamp(time_old)).split(' ')
				print(only_time[1]+"\t\t"+str(calls_in)+"\t\t"+str(calls_out)+"\t\t"+str(calls_all))
				print_call = 0
#			print(str(datetime.fromtimestamp(key_all))+"\t"+str(dict_all[key_all]['in'])+"\t"+str(dict_all[key_all]['out'])+"\t"+str(dict_all[key_all]['all'])+"\t-\t",end = '')
			only_date = str(datetime.fromtimestamp(key_all)).split(' ')
			if dict_all[key_all]['all'] >= 6:
				if only_date[0] != dtae_new:
					if start_yes == 0:
						print('|_________|______________________|_______________|_________________|________|')
						start_yes = 1
					else:
						print('_____________________________________________________________________________')
					print(str(datetime.fromtimestamp(key_all))+" - ",end = '')
					dtae_new = only_date[0]
				else:
					print('           '+only_date[1]+" - ",end = '')
				print_call = 1
#		else:
#			print('Error!',end='')
	time_old = key_all
	calls_in = dict_all[key_all]['in']
	calls_out = dict_all[key_all]['out']
	calls_all = dict_all[key_all]['all']
#only_time = str(datetime.fromtimestamp(key_all)).split(' ')
#print(only_time[1]+"\t"+str(calls_in)+"\t"+str(calls_out)+"\t"+str(calls_all))
print('______________________________________________________________________________')


