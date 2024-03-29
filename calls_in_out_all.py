#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
import subprocess
import pymysql
import sys
import re
import smtplib
import email.message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

server = smtplib.SMTP('smtp.gmail.com:587')
from datetime import datetime
date_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%H%M%S")
array = []
dict_number = {}
dir_conf = '/opt/asterisk/script/'
number_all = set(['all'])
number_all_ok = 0
dictionary_max = {}
dictionary_ringgroups = {}
dictionary_users = {}
dictionary_incoming = {}
email_report = ''
passwordemailreport = ''
sendto = ''
sendfrom = ''
sendsmtp = ''

def hms(secs):
	days = secs//86400
	hours = (secs - days*86400)//3600
	minutes = (secs - days*86400 - hours*3600)//60
	seconds = secs - days*86400 - hours*3600 - minutes*60
	result = ("{0} day{1}, ".format(days, "s" if days!=1 else "") if days else "") + \
	("{0} hour{1}, ".format(hours, "s" if hours!=1 else "") if hours else "") + \
	("{0} minute{1}, ".format(minutes, "s" if minutes!=1 else "") if minutes else "") + \
	("{0} second{1} ".format(seconds, "s" if seconds!=1 else "") if seconds else "")
	return result
	
freepbx_pass = open (str(dir_conf)+'freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	result_line=re.match(r'sendfrom = ', line)
	if result_line is not None:
		param_sendfrom=line.split(' = ')
		sendfrom=param_sendfrom[1]
	result_line=re.match(r'sendsmtp = ', line)
	if result_line is not None:
		param_sendsmtp=line.split(' = ')
		sendsmtp=param_sendsmtp[1]
	result_line=re.match(r'passwordemailreport = ', line)
	if result_line is not None:
		param_passwordemailreport=line.split(' = ')
		passwordemailreport=param_passwordemailreport[1]
	result_line=re.match(r'sendto = ', line)
	if result_line is not None:
		param_sendto=line.split(' = ')
		sendto=param_sendto[1]
	result_line=re.match(r'dict_number = ', line)
	if result_line is not None:
		param_fixedcid=line.split(' = ')
		dict_number_array=param_fixedcid[1].split(',')
		for num_lin in dict_number_array:
			number_line=num_lin.split(':')
			dict_number[str(number_line[0])]=int(number_line[1])
			number_all.add(str(number_line[0]))
			if number_line[0] not in dictionary_max:
				dictionary_max[number_line[0]] = {'in':0, 'out':0, 'all':0}
	result_line=re.match(r'email_report = ', line)
	if result_line is not None:
		param_email_report=line.split(' = ')
		email_report = param_email_report[1]
freepbx_pass.close()

for param in sys.argv:
	array.append(param)
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

for row_number_all in number_all:
	if row_number_all == array[5]:
		number_all_ok = 1
		break
if number_all_ok == 0:
	print('Нет такого номера на сервере!')
	print('Возможные варианты:'+str(number_all))
	sys.exit()

result_line=re.match(r'\d{1,3}$', array[6])
if result_line is None:
	print('Количество линий может быть только число 1 - 999!')
	sys.exit()

asteriskdb = pymysql.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor_ringgroups = asteriskdb.cursor()
cursor_ringgroups.execute("SELECT grpnum, description, grplist FROM ringgroups")
if cursor_ringgroups != '':
	for row_ringgroups in cursor_ringgroups:
		dictionary_ringgroups[row_ringgroups[0]] = {}
		dictionary_ringgroups[row_ringgroups[0]]['coment'] = row_ringgroups[1]
		dictionary_ringgroups[row_ringgroups[0]]['extension'] = row_ringgroups[2]
#		print(row_ringgroups[0]+' '+row_ringgroups[1]+' '+row_ringgroups[2])
else:
	print('Warning_01: Ring Groups отсутствуют на сервере!')
cursor_ringgroups.close()

cursor_users = asteriskdb.cursor()
cursor_users.execute("SELECT extension, name FROM users;")
if cursor_users != '':
	for row_users in cursor_users:
		dictionary_users[row_users[0]] = {}
		dictionary_users[row_users[0]] = row_users[1]
else:
	print('Warning_03: Внутренние номера отсутствуют на сервере!')
cursor_users.close()

cursor_incoming = asteriskdb.cursor()
cursor_incoming.execute("SELECT extension, destination FROM incoming WHERE destination LIKE '%ext-group%' or destination LIKE '%from-did-direct%'")
if cursor_incoming != '':
	for row_incoming in cursor_incoming:
		incoming = row_incoming[1].split(',')
		dictionary_incoming[row_incoming[0]] = {}
		dictionary_incoming[row_incoming[0]] = incoming[1]
#		print(row_incoming[0]+' '+incoming[1])
else:
	print('Warning_02: На сервере нет входящих маршрутов на группы вызова и внутренние номера!')
cursor_incoming.close()
asteriskdb.close()

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
date_new = '1970.01.01'
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
start_yes = 0
calls_log=open(str(dir_conf)+'log/calls/'+date_time+'.log', 'a')

print('1. Отчет по перегруженным линиям на номерах:')
print(' __________________________________________________________________________')
print('|           |          |                   |          |           |        |')
print('|   Номер   |   Дата   |  Временной период | Входящие | Исходящие | Вх+Исх |')
print('|___________|__________|___________________|__________|___________|________|')
calls_log.write('1. Отчет по перегруженным линиям на номерах:'+"\r\n")
calls_log.write(' __________________________________________________________________________'+"\r\n")
calls_log.write('|           |          |                   |          |           |        |'+"\r\n")
calls_log.write('|   Номер   |   Дата   |  Временной период | Входящие | Исходящие | Вх+Исх |'+"\r\n")
calls_log.write('|___________|__________|___________________|__________|___________|________|'+"\r\n")
total = 0
number_old = 0
for key_number in sorted(dictionary.keys()):
	time_old = 0
	calls_in = 0
	calls_out = 0
	calls_all = 0
	print_call = 0
	key_number_yes = 0
	key_date_st = 0
	if number_old == 0:
		number_old = key_number
	for key_date in sorted(dictionary[key_number].keys()):
		if time_old == 0:
			if dictionary[key_number][key_date]['all'] > 1:
				if total != 0:
					print("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total)))
					print(' __________________________________________________________________________')
					calls_log.write("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total))+"\r\n")
					calls_log.write(' __________________________________________________________________________'+"\r\n")
					total = 0
					number_old = key_number
				key_date_st = key_date
				if dictionary_incoming.get(key_number) is not None:
					if dictionary_ringgroups.get(dictionary_incoming[key_number]) is not None:
						print(' Номер '+key_number+' закреплен за группой \''+dictionary_ringgroups[dictionary_incoming[key_number]]['coment']+'\', в которую входят номера: \''+dictionary_ringgroups[dictionary_incoming[key_number]]['extension']+'\'')
						calls_log.write(' Номер '+key_number+' закреплен за группой \''+dictionary_ringgroups[dictionary_incoming[key_number]]['coment']+'\', в которую входят номера: \''+dictionary_ringgroups[dictionary_incoming[key_number]]['extension']+'\''+"\r\n")
					else:
						print(' Номер '+key_number+' закреплен за \''+dictionary_users[dictionary_incoming[key_number]]+'\' - \''+dictionary_incoming[key_number]+'\'')
						calls_log.write(' Номер '+key_number+' закреплен за \''+dictionary_users[dictionary_incoming[key_number]]+'\' - \''+dictionary_incoming[key_number]+'\''+"\r\n")
				print("%+12s %+19s %+1s" % (str(key_number), str(datetime.fromtimestamp(key_date)), '-'), end = '')
				calls_log.write("%+12s %+19s %+1s" % (str(key_number), str(datetime.fromtimestamp(key_date)), '-'))
				number_old = key_number
				date_new = only_date[0]
				key_number_yes = key_number
				print_call = 1
		else:
			if((calls_in == dictionary[key_number][key_date]['in'] == 0) and (calls_out == dictionary[key_number][key_date]['out'] == 0) and (calls_all == dictionary[key_number][key_date]['all'] == 0)):
				calls_tmp = 0
			elif(((time_old + 1) != key_date) or (calls_in != dictionary[key_number][key_date]['in']) or (calls_out != dictionary[key_number][key_date]['out']) or (calls_all != dictionary[key_number][key_date]['all'])):
				if print_call == 1 and calls_all > 1:
					only_time = str(datetime.fromtimestamp(time_old)).split(' ')
					time_sec = int(time_old) - int(key_date_st) + 1
					total = total + time_sec
					print("%+9s %+6s %+10s %+8s" % (only_time[1], str(calls_in), str(calls_out), str(calls_all)))
					calls_log.write("%+9s %+6s %+10s %+8s" % (only_time[1], str(calls_in), str(calls_out), str(calls_all))+"\r\n")
					print_call = 0
				only_date = str(datetime.fromtimestamp(key_date)).split(' ')
##				if key_number in dict_number:
				pr_key_number = key_number
##				else:
##					pr_key_number = '!'+str(key_number)
				if ((key_number in dict_number) and (dictionary[key_number][key_date]['all'] >= dict_number[key_number])) or ((key_number not in dict_number) and (dictionary[key_number][key_date]['all'] > 1)):
					if key_number_yes != key_number:
						if total != 0:
							print("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total)))
							print(' __________________________________________________________________________')
							calls_log.write("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total))+"\r\n")
							calls_log.write(' __________________________________________________________________________'+"\r\n")
							total = 0
							number_old = key_number
						key_date_st = key_date
						if dictionary_incoming.get(key_number) is not None:
							if dictionary_ringgroups.get(dictionary_incoming[key_number]) is not None:
								print(' Номер '+key_number+' закреплен за группой \''+dictionary_ringgroups[dictionary_incoming[key_number]]['coment']+'\', в которую входят номера: \''+dictionary_ringgroups[dictionary_incoming[key_number]]['extension']+'\'')
								calls_log.write(' Номер '+key_number+' закреплен за группой \''+dictionary_ringgroups[dictionary_incoming[key_number]]['coment']+'\', в которую входят номера: \''+dictionary_ringgroups[dictionary_incoming[key_number]]['extension']+'\''+"\r\n")
							else:
								print(' Номер '+key_number+' закреплен за \''+dictionary_users[dictionary_incoming[key_number]]+'\' - \''+dictionary_incoming[key_number]+'\'')
								calls_log.write(' Номер '+key_number+' закреплен за \''+dictionary_users[dictionary_incoming[key_number]]+'\' - \''+dictionary_incoming[key_number]+'\''+"\r\n")
						print("%+12s %+19s %+1s" % (str(pr_key_number), str(datetime.fromtimestamp(key_date)), '-'),end = '')
						calls_log.write("%+12s %+19s %+1s" % (str(pr_key_number), str(datetime.fromtimestamp(key_date)), '-'))
						number_old = key_number
						date_new = only_date[0]
						key_number_yes = key_number
					else:
						if only_date[0] != date_new:
							key_date_st = key_date
							print("%+12s %+19s %+1s" % ('', str(datetime.fromtimestamp(key_date)), '-'),end = '')
							calls_log.write("%+12s %+19s %+1s" % ('',str(datetime.fromtimestamp(key_date)),'-'))
							date_new = only_date[0]
						else:
							key_date_st = key_date
							print("%+12s %+19s %+1s" % ('', only_date[1], '-'),end = '')
							calls_log.write("%+12s %+19s %+1s" % ('', only_date[1], '-'))
					print_call = 1
		time_old = key_date
		calls_in = dictionary[key_number][key_date]['in']
		calls_out = dictionary[key_number][key_date]['out']
		calls_all = dictionary[key_number][key_date]['all']
	if print_call == 1:
		only_time = str(datetime.fromtimestamp(key_date)).split(' ')
		print("%+9s %+6s %+10s %+8s" % (only_time[1], str(calls_in), str(calls_out), str(calls_all)))
		calls_log.write("%+9s %+6s %+10s %+8s" % (only_time[1], str(calls_in), str(calls_out), str(calls_all))+"\r\n")
if total != 0:
	print("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total)))
print(' ==========================================================================')
print("\n"+'2. Отчет по суммарной загрузке всех линий на АТС:')
print(' _______________________________________________________________________')
print('|          |                   |        |          |           |        |')
print('|   Дата   |  Временной период | Секунд | Входящие | Исходящие | Вх+Исх |')
print('|__________|___________________|________|__________|___________|________|')
calls_log.write("%+66s %+14s" % (' Суммарное время периодов, когда на номере '+number_old+' все линии были заняты: ', hms(total))+"\r\n")
total = 0
calls_log.write(' =========================================================================='+"\r\n")
calls_log.write("\n"+'2. Отчет по суммарной загрузке всех линий на АТС:'+"\r\n")
calls_log.write(' _______________________________________________________________________'+"\r\n")
calls_log.write('|          |                   |        |          |           |        |'+"\r\n")
calls_log.write('|   Дата   |  Временной период | Секунд | Входящие | Исходящие | Вх+Исх |'+"\r\n")
calls_log.write('|__________|___________________|________|__________|___________|________|'+"\r\n")
dict_all = {}
date_new = '1970.01.01'
#{'in': 0,'out': 0,'all':0}
for key_number in sorted(dictionary.keys()):
#	print(key_number)
	if array[5] == 'all':
		for key_date in sorted(dictionary[key_number].keys()):
			if key_date not in dict_all:
				dict_all[key_date] = {'in':0, 'out':0, 'all':0}
##				print("\t"+str(key_date)+"\t"+str(dictionary[key_number][key_date]))
			dict_all[key_date]['in'] = int(dict_all[key_date]['in']) + int(dictionary[key_number][key_date]['in'])
			dict_all[key_date]['out'] = int(dict_all[key_date]['out']) + int(dictionary[key_number][key_date]['out'])
			dict_all[key_date]['all'] = int(dict_all[key_date]['all']) + int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])
			if key_number not in dictionary_max:
				dictionary_max[key_number] = {'in':0, 'out':0, 'all':0}
			if int(dictionary_max[key_number]['all']) < (int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])):
				dictionary_max[key_number]['in'] = int(dictionary[key_number][key_date]['in'])
				dictionary_max[key_number]['out'] = int(dictionary[key_number][key_date]['out'])
				dictionary_max[key_number]['all'] = int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])
	else:
		if key_number == array[5]:
			for key_date in sorted(dictionary[key_number].keys()):
				if key_date not in dict_all:
					dict_all[key_date] = {'in':0, 'out':0, 'all':0}
				dict_all[key_date]['in'] = int(dict_all[key_date]['in']) + int(dictionary[key_number][key_date]['in'])
				dict_all[key_date]['out'] = int(dict_all[key_date]['out']) + int(dictionary[key_number][key_date]['out'])
				dict_all[key_date]['all'] = int(dict_all[key_date]['all']) + int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])
				if key_number not in dictionary_max:
					dictionary_max[key_number] = {'in':0, 'out':0, 'all':0}
				if int(dictionary_max[key_number]['all']) < (int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])):
					dictionary_max[key_number]['in'] = int(dictionary[key_number][key_date]['in'])
					dictionary_max[key_number]['out'] = int(dictionary[key_number][key_date]['out'])
					dictionary_max[key_number]['all'] = int(dictionary[key_number][key_date]['in']) + int(dictionary[key_number][key_date]['out'])

time_old = 0
calls_in = 0
calls_out = 0
calls_all = 0
print_call = 0
start_yes = 0
time_start_count = 0
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
				count_sec = int(time_old) - int(time_start_count) + 1
				print("%+9s %+7s %+7s %+10s %+10s" % (only_time[1], count_sec, str(calls_in), str(calls_out), str(calls_all)))
				calls_log.write("%+9s %+7s %+7s %+10s %+10s" % (only_time[1], count_sec, str(calls_in), str(calls_out), str(calls_all))+"\r\n")
				print_call = 0
#			print(str(datetime.fromtimestamp(key_all))+"\t"+str(dict_all[key_all]['in'])+"\t"+str(dict_all[key_all]['out'])+"\t"+str(dict_all[key_all]['all'])+"\t-\t",end = '')
			only_date = str(datetime.fromtimestamp(key_all)).split(' ')
			if dict_all[key_all]['all'] >= int(array[6]):
				time_start_count = key_all
				if only_date[0] != date_new:
					if start_yes == 0:
						start_yes = 1
					else:
						print(' _______________________________________________________________________')
						calls_log.write(' _______________________________________________________________________'+"\r\n")
					print("%+20s %+1s" % (str(datetime.fromtimestamp(key_all)), '-') ,end = '')
					calls_log.write("%+20s %+1s" % (str(datetime.fromtimestamp(key_all)), '-'))
					date_new = only_date[0]
				else:
					print("%+20s %+1s" % (only_date[1], '-'), end = '')
					calls_log.write("%+20s %+1s" % (only_date[1], '-'))
				print_call = 1
#		else:
#			print('Error!',end='')
	time_old = key_all
	calls_in = dict_all[key_all]['in']
	calls_out = dict_all[key_all]['out']
	calls_all = dict_all[key_all]['all']
if print_call == 1:
	only_time = str(datetime.fromtimestamp(key_all)).split(' ')
	count_sec = int(key_all) - int(time_start_count) + 1
	print("%+9s %+7s %+7s %+10s %+10s" % (only_time[1], count_sec, str(calls_in), str(calls_out), str(calls_all)))
	calls_log.write("%+9s %+7s %+7s %+10s %+10s" % (only_time[1], count_sec, str(calls_in), str(calls_out), str(calls_all))+"\r\n")
print(' =======================================================================')
calls_log.write(' ======================================================================='+"\r\n")

print("\n"+'3. Отчет по загрузке всех линий на всех номерах:')
print(' ___________________________________________________________________')
print('|           |          |           |        |                       |')
print('|   Номер   | Входящие | Исходящие | Вх+Исх | Всего линий на номере |')
print('|___________|__________|___________|________|_______________________|')
calls_log.write("\n"+'3. Отчет по загрузке всех линий на всех номерах:'+"\r\n")
calls_log.write(' ___________________________________________________________________'+"\r\n")
calls_log.write('|           |          |           |        |                       |'+"\r\n")
calls_log.write('|   Номер   | Входящие | Исходящие | Вх+Исх | Всего линий на номере |'+"\r\n")
calls_log.write('|___________|__________|___________|________|_______________________|'+"\r\n")

for key_number in sorted(dict_number.keys()):
	for key_number_max in sorted(dictionary_max.keys()):
		if key_number == key_number_max:
			print("%+12s %+6s %+10s %+9s %+15s" % (str(key_number), str(dictionary_max[key_number_max]['in']), str(dictionary_max[key_number_max]['out']), str(dictionary_max[key_number_max]['all']), str(dict_number[key_number])))
			calls_log.write("%+12s %+6s %+10s %+9s %+15s" % (str(key_number),str(dictionary_max[key_number_max]['in']), str(dictionary_max[key_number_max]['out']), str(dictionary_max[key_number_max]['all']), str(dict_number[key_number]))+"\r\n")

calls_log.close()

#os.system("/usr/bin/sendEmail -f fax_out\@$domen -t $user_email -u Исходящий факс -o message-charset=utf-8 
#	-m \"\<html\>Для отправки факсимильного сообщения, в процессе разговора, необходимо перевести вызов на номер: $num\<br\>\<br\>$comment\<\/html\>\" 
#	-s localhost -a $dir_tiff/$num.pdf")
	
if email_report != '':
	email_from = email_report.split('@')
	if(array[5] == 'all'):
		email_content = '<html>Отчет сформирован за период: '+array[1]+' '+array[2]+' - '+array[3]+' '+array[4]+'<br>По всем номерам. <br>Отчет №2, по загрузке линий на АТС, сформирован за те временные периоды, в каторые загрузка линий была >= '+array[6]+' <br><br></html>'
	else:
		email_content = '<html>Отчет сформирован за период: '+array[1]+' '+array[2]+' - '+array[3]+' '+array[4]+'<br>По номеру: '+array[5]+'<br>Отчет №2, по загрузке линий на АТС, сформирован за те временные периоды, в каторые загрузка линий была >= '+array[6]+' <br><br></html>'

	msg = MIMEMultipart()
	msg['From'] = sendfrom
	msg['To'] = sendto
	msg['Subject'] = 'Отчеты по загрузке линий на АТС'
	password = passwordemailreport

	msg.attach(MIMEText(email_content, "html"))
	
	with open(dir_conf+'log/calls/'+date_time+'.log') as f:
	    file = MIMEText(f.read())
	
	file.add_header('content-disposition', 'attachment', filename = date_time+'.log')
	msg.attach(file)
	
	s = smtplib.SMTP(sendsmtp)
	s.starttls()
	s.login(msg['From'], password)
	s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
	