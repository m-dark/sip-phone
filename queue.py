#!/usr/bin/env python3.6
#yum list python36*
#yum install python36u-pip
#pip3.6 install --upgrade pip
#pip3.6 install pymysql

import os
import subprocess
import pymysql
import sys
import re
import datetime
import logging
from datetime import timedelta
from datetime import datetime
#import xml.etree.ElementTree as ET
from urllib import request, parse
#import urllib.request
#import urllib.parse
import ssl
URL = "https://sedrestore.egov66.ru/freepbx/"
data = ''
#headers = {}
#headers['Content-Type'] = 'application/xml'
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/'
array = []
linkedid = ''
timestart = ''
job = dict()
log = logging.getLogger("QueueCalls")
fh = logging.FileHandler(dir_conf+'log/post.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(name)s:%(message)s"))
log.addHandler(fh)
log.setLevel(logging.DEBUG)

if(sys.argv[2] == '10050'):
	result_date_start=re.match(r'(\d+\.\d+)', sys.argv[1])
	if result_date_start is None:
		print('Error_01: linkedid '+sys.argv[1]+' не соответствует формату!')
		sys.exit()
	else:
		linkedid = sys.argv[1]
		print(sys.argv[1]);

	db = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
	cursor = db.cursor()
	cursor.execute("SELECT calldate, dst, src, billsec FROM cdr WHERE (linkedid = %s) AND (disposition = %s)", (linkedid, 'ANSWERED'))
	for row in cursor:
		if job.get(row[1]) is None:
			job[row[1]] = {}
			job[row[1]]['timestart'] = row[0]
			job[row[1]]['src'] = row[2]
			job[row[1]]['billsec'] = row[3]
		else:
			job[row[1]]['billsec'] = job[row[1]]['billsec'] + row[3]
		print(row)

	for number_b in job:
		if number_b == '10050':
			print('Общую продолжительность вызова на номер 10050 не отправляем!')
		else:
			try:
				a = job[number_b]['timestart']
				b = timedelta(seconds=job[number_b]['billsec'])
				timestop = a + b
##		print(str(job[number_b]['timestart'])+'    '+str(timestop)+'    '+ number_b+' '+str(job[number_b]['src'])+' '+str(job[number_b]['billsec']))

#				gcontext = ssl.SSLContext()
				data = '<?xml version="1.0" encoding="utf-8"?>'+"\n"
				data += '<content Version="80903">'+"\n"
				data += '  <call commcount="3" taskcount="0">'+"\n"
				data += '    <property_simple key="direction" value="1" name="cdIncoming" />'+"\n"
				data += '    <property_simple key="linenumber" value="'+number_b+'" />'+"\n"
				data += '    <property_simple key="callerid" value="'+job[number_b]['src']+'" />'+"\n"
				data += '    <property_simple key="timestart" value="'+str(job[number_b]['timestart'])+'" />'+"\n"
				data += '    <property_simple key="timestop" value="'+str(timestop)+'" />'+"\n"
				data += '    <property_simple key="totalsec" value="'+str(job[number_b]['billsec'])+'" />'+"\n"
				data += '    <property_simple key="userid" value="'+number_b+'" />'+"\n"
				data += '  </call>'+"\n"
				data += '</content>'+"\n"
				print(data)
				
				post_data = parse.urlencode({'xml':data}).encode("utf-8")
				req = request.Request(URL, data=post_data)
				response = request.urlopen(url=URL, data=post_data)

				print(response.read().decode("utf-8"))
				print(response.code)
			except Exception:
				print("Error occuried during web request!")
				print(sys.exc_info()[1])

		log.info('Тот номер:    '+sys.argv[2]+' ID: '+sys.argv[1]+' номер B:'+number_b+' продолжительность:'+str(job[number_b]['billsec'])+' секунд')
else:
	log.info('Не тот номер: '+sys.argv[2]+' А вот ID: '+sys.argv[1])
