#!/usr/bin/env python3.6
#yum list python36*
#yum install python36u-pip
#pip3.6 install --upgrade pip
#pip3.6 install pymysql
#chmod 767 /opt/asterisk/script/log
#copy queue.py to /var/lib/asterisk/agi-bin/queue.py

#Add /etc/asterisk/extensions_custom.conf
#[sub-call-from-cid-ended]
#exten => s,1,GotoIf($[«${ARG1}» = «» | «${ARG2}» = «»]?end)
#exten => s,n,NoOp(-------------------------------------------------------Call from ${ARG1} to ${ARG2} ID ${UNIQUEID}----------------------------------------------------------------------)
#exten => s,n,AGI(queue.py,${UNIQUEID},${ARG2})
#exten => n(end),Return
#;--== end of [sub-call-from-cid-ended] ==--;

#And Add /etc/asterisk/extensions_override_freepbx.conf
#to [ext-did-0002]
#>exten => 3110050,n,ExecIf($["${CRM_DIRECTION}"="INBOUND"]?Set(CHANNEL(hangup_handler_push)=crm-hangup,s,1))
#!!!exten => 3110050,n,Set(CHANNEL(hangup_handler_push)=sub-call-from-cid-ended,s,1(${CALLERID(num)},${EXTEN}))
#>exten => 3110050,n(dest-ext),Goto(ext-queues,10050,1)


import os
import subprocess
import pymysql
import sys
import re
import datetime
import logging
from datetime import timedelta
from datetime import datetime
from urllib import request, parse
import ssl
URL = "https://sedrestore.egov66.ru/freepbx/"
data = ''
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

if((sys.argv[2] == '10050') or (sys.argv[2] == '3110050') or (sys.argv[2] == '3120996')):
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

		log.info(' Номер входящего маршрута: '+sys.argv[2]+' ID вызова: '+sys.argv[1]+' номер A: '+job[number_b]['src']+' номер B: '+number_b+' продолжительность разговора: '+str(job[number_b]['billsec'])+' сек.')
else:
	log.warning(' Отправка информации по маршруту: '+sys.argv[2]+' не настроена, ID вызова: '+sys.argv[1])
