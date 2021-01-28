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
#reload(sys)
#sys.setdefaultencoding('utf-8')
from datetime import datetime
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/autoprovisioning/'
array = []
linkedid = ''
job = dict()
result_date_start=re.match(r'(\d+\.\d\d\d\d)', sys.argv[1])
if result_date_start is None:
	print('Error_01: linkedid '+sys.argv[1]+' не соответствует формату!')
	sys.exit()
else:
	linkedid = sys.argv[1]
	print(sys.argv[1]);

db = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT dst, src, billsec FROM cdr WHERE (linkedid = %s) AND (disposition = %s)", (linkedid, 'ANSWERED'))
for row in cursor:
	if job.get(row[0]) is None:
		job[row[0]] = {}
		job[row[0]]['src'] = row[1]
		job[row[0]]['billsec'] = row[2]
	else:
		job[row[0]]['billsec'] = job[row[0]]['billsec'] + row[2]
	print(row)

for number_a in job:
	print(number_a+' '+str(job[number_a]['src'])+' '+str(job[number_a]['billsec']))