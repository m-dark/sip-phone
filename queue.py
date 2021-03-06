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
import re
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
import time
URL = ''
data = ''
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/'
array = []
queue_number_no_mess_push_i = []
linkedid = ''
timestart = ''
queue_db = ''
job = dict()
log = logging.getLogger("QueueCalls")
fh = logging.FileHandler(dir_conf+'log/post.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(name)s: %(message)s"))
log.addHandler(fh)
log.setLevel(logging.DEBUG)

result_date_start=re.match(r'(\d+\.\d+)', sys.argv[1])
if result_date_start is None:
	print('Error_01: linkedid '+sys.argv[1]+' не соответствует формату!')
	log.error('ID: '+sys.argv[1]+' не соответствует формату!')
	sys.exit()
else:
	linkedid = sys.argv[1]
	print(sys.argv[1])
#	log.info('Вызов с ID: '+sys.argv[1]+' номер B: '+ sys.argv[2])

freepbx_pass = open (str(dir_conf)+'autoprovisioning/freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	result_line=re.match(r'queue_db = ', line)
	if result_line is not None:
		param_queue_db=line.split(' = ')
		queue_db=param_queue_db[1]
	result_line=re.match(r'queue_url = ', line)
	if result_line is not None:
		param_queue_url=line.split(' = ')
		URL=param_queue_url[1]
	result_line=re.match(r'queue_number_no_mess_push = ', line)
	if result_line is not None:
		queue_number_no_mess_push_array = line.split(' = ')
		queue_number_no_mess_push_1 = queue_number_no_mess_push_array[1]
		result_line=re.search(',', queue_number_no_mess_push_1)
		if result_line is not None:
			queue_number_no_mess_push_i=queue_number_no_mess_push_1.split(',')
		else:
			queue_number_no_mess_push_i.append(queue_number_no_mess_push_1)
freepbx_pass.close()

time.sleep(6)
log.info('1 Информация по вызову с ID: '+str(sys.argv[1])+' Номер: '+str(sys.argv[2]))
db = pymysql.connect(host="localhost", user="root", passwd="", db=queue_db, charset='utf8')
cursor = db.cursor()
#cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND (uniqueid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal')) OR ((dst REGEXP '^[0-9]+') AND (uniqueid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/'))", (linkedid, 'ANSWERED', linkedid, 'ANSWERED'))
cursor.execute("SELECT calldate, dst, src, billsec, lastdata, dstchannel FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND ((uniqueid = %s) AND (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal') AND (dstchannel NOT REGEXP '^Local/')) OR ((dst REGEXP '^[0-9]+') AND ((uniqueid = %s) AND (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/') AND (dstchannel NOT REGEXP '^Local/'))", (linkedid, linkedid, 'ANSWERED', linkedid, linkedid, 'ANSWERED'))
#2021.04.26 cursor.execute("SELECT calldate, dst, src, billsec, lastdata, dstchannel FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal') AND (dstchannel NOT REGEXP '^Local/')) OR ((dst REGEXP '^[0-9]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/') AND (dstchannel NOT REGEXP '^Local/'))", (linkedid, 'ANSWERED', linkedid, 'ANSWERED'))
####cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal') AND (dstchannel NOT REGEXP '^Local/FM')) OR ((dst REGEXP '^[0-9]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/') AND (dstchannel NOT REGEXP '^Local/FM'))", (linkedid, 'ANSWERED', linkedid, 'ANSWERED'))

#cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal')) OR ((dst REGEXP '^[0-9]+') AND (linkedid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/'))", (linkedid, 'ANSWERED', linkedid, 'ANSWERED'))

#cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[1][0][0]+') AND ((uniqueid = %s) OR (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal')) OR ((dst REGEXP '^[0-9]+') AND ((uniqueid = %s) OR (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/'))", (linkedid, linkedid, 'ANSWERED', linkedid, linkedid, 'ANSWERED'))
#cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[0-9]+') AND ((uniqueid = %s) OR (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal')) OR ((dst REGEXP '^[0-9]+') AND ((uniqueid = %s) OR (linkedid = %s)) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/'))", (linkedid, linkedid, 'ANSWERED', linkedid, linkedid, 'ANSWERED'))
#cursor.execute("SELECT calldate, dst, src, billsec, lastdata FROM cdr WHERE ((dst REGEXP '^[0-9]+') AND (uniqueid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext != 'from-internal')) OR ((dst REGEXP '^[0-9]+') AND (uniqueid = %s) AND (disposition = %s) AND (billsec != '0') AND (dcontext = 'from-internal') AND (channel NOT REGEXP '^PJSIP/'))", (linkedid, 'ANSWERED', linkedid, 'ANSWERED'))
#cursor.execute("SELECT calldate, dst, src, billsec FROM cdr WHERE (uniqueid = %s) AND (disposition = %s) AND (billsec != '0')", (linkedid, 'ANSWERED'))
for row in cursor:
	number_b_new = row[1]
	number_b_transfer = ''
	result=re.match(r'Local/FMPR-', row[4])
	if result is not None:
		param=row[4].split('@')
		number_local=param[0].split('-')
		number_b_transfer = number_local[1]

	result=re.match(r'PJSIP/', row[4])
	if result is not None:
		param=row[4].split('@')
		number_local=param[0].split(':')
		number_b_transfer = number_local[1]

	result=re.match(r'SIP/', row[4])
	if result is not None:
		param=row[4].split(',')
		number_trans=param[0].split('/')
		number_b_transfer = number_trans[2]
	if number_b_transfer != '' and number_b_transfer != row[1]:
		number_b_new = number_b_transfer
	if job.get(number_b_new) is None:
		job[number_b_new] = {}
		job[number_b_new]['timestart'] = row[0]
		job[number_b_new]['src'] = row[2]
		job[number_b_new]['billsec'] = row[3]
	else:
		job[number_b_new]['billsec'] = job[number_b_new]['billsec'] + row[3]
	print(row)

for number_b in job:
	skip = 'no'
	for number_file in queue_number_no_mess_push_i:
		if number_b == number_file:
			skip = 'yes'
	if (skip == 'yes'):
		print('Общую продолжительность вызова на номер 10050 не отправляем!')
	else:
		try:
			a = job[number_b]['timestart']
			b = timedelta(seconds=job[number_b]['billsec'])
			timestop = a + b
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
			log.info('1 Номер входящего маршрута: '+sys.argv[2]+' ID вызова: '+sys.argv[1]+' номер A: '+job[number_b]['src']+' номер B: '+number_b+' продолжительность разговора: '+str(job[number_b]['billsec'])+' сек.')
		except Exception:
			print("Error occuried during web request!")
			print(sys.exc_info()[1])
			log.error('1 Информация по вызову с ID: '+str(sys.argv[1])+' не отправлена, так как '+URL+' вернул ошибку: '+str(sys.exc_info()[1]))
			sys.exit()
cursor.close()
db.close()
