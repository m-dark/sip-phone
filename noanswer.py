# -*- coding: utf-8 -*-
#кодировка
import sys
import os
import re
reload(sys)
sys.setdefaultencoding('utf-8')
import MySQLdb
import subprocess
from datetime import datetime
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/';
fixedcid_def = '';
fw_auto = 0;
call_waiting_i = []
freepbx_pass = open (str(dir_conf)+'freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	result_line=re.match(r'fixedcid = \d+', line)
	if result_line is not None:
		param_fixedcid=line.split(' = ')
		fixedcid_def=param_fixedcid[1]
	result_line=re.match(r'fw_auto = \d', line)
	if result_line is not None:
		param_fw_auto=line.split(' = ')
		fw_auto=param_fw_auto[1]
	result_line=re.match(r'call_waiting_invisible = \d+', line)
	if result_line is not None:
		param_call_waiting_invisible=line.split(' = ')
		call_waiting_invisible=param_call_waiting_invisible[1]
		result_line=re.match(r'\d+,', call_waiting_invisible)
		if result_line is not None:
			call_waiting_i=call_waiting_invisible.split(',')
		else:
			call_waiting_i.append(call_waiting_invisible)
freepbx_pass.close()

list_ring_strategy = ['ringallv2','ringallv2-prim','ringall','ringall-prim','hunt','hunt-prim','memoryhunt-prim','firstavailable','firstnotonphone']
db = MySQLdb.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor = db.cursor()
restart=0

#Call Waiting

check_cw=subprocess.check_output('/usr/sbin/rasterisk -x "database show CW"',shell=True,universal_newlines=True)
line_cw=check_cw.split('\n')
for line_enable_cw in line_cw:
	call_waiting_enabled_yes = 0
#	result_cw=re.match(r'/CW/\d+', line_enable_cw)
	result_cw=re.search(r'ENABLED', line_enable_cw)
	if result_cw is not None:
		new_line_enable_cw = line_enable_cw.split(' ')
		new_line_enable_cw = new_line_enable_cw[0].split('/CW/')
		for no_call_waiting in call_waiting_i:
			if new_line_enable_cw[1] == no_call_waiting:
				call_waiting_enabled_yes = 1
		if call_waiting_enabled_yes == 0:
#			upd_cwdb='/usr/sbin/rasterisk -x "database put CW '+new_line_enable_cw[1]+' DISABLED'
			upd_cwdb='/usr/sbin/rasterisk -x "database del CW '+new_line_enable_cw[1]
			subprocess.call(upd_cwdb+'"', shell=True)
			restart=1
<<<<<<< HEAD
			file_log_cw=open(str(dir_conf)+'log/busy_dest.log', 'a')
=======
			file_log_cw=open('/opt/asterisk/script/log/busy_dest.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
			file_log_cw.write(str(date_time+"\t"+'Для номера '+new_line_enable_cw[1]+' в Расширенных настройках выключили Call Waiting (DISABLED)'+"\n"))
			file_log_cw.close()
busy_dest_sql="SELECT extension FROM users WHERE `busy_dest` = ''"
cursor.execute(busy_dest_sql)
for row in cursor:
	call_waiting_no_yes = 0
	for no_call_waiting in call_waiting_i:
		if row[0] == no_call_waiting:
			call_waiting_no_yes = 1
	if call_waiting_no_yes == 0:
#		upd_busy_dest_sql="""UPDATE users,devices SET users.name='%(name)s',devices.description='%(name)s' WHERE users.extension=devices.id AND users.extension='%(num)s'"""%{"name":row[2],"num":row[0]}
		upd_busy_dest_sql="""UPDATE users SET users.busy_dest='%(b_dest)s' WHERE users.extension='%(num)s'"""%{"b_dest":'my-call-hold1,s,1',"num":row[0]}
		cursor.execute(upd_busy_dest_sql)
		db.commit()
		restart=1
<<<<<<< HEAD
		file_log_busy_dest=open(str(dir_conf)+'log/busy_dest.log', 'a')
=======
		file_log_busy_dest=open('/opt/asterisk/script/log/busy_dest.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
		file_log_busy_dest.write(str(date_time+"\t"+'Для номера '+row[0]+' в Расширенных настройках включили при BUSY дополнительное назначение my-call-hold'+"\n"))
		file_log_busy_dest.close()
db.commit()
#FW
#
if fw_auto == "1":
	sql="SELECT default_extension,cell from userman_users WHERE `cell` !='' AND `default_extension` !='none'"
	cursor.execute(sql)
	for row in cursor:
		result=re.match(r"^(\d+(-\d+)*),\d{1,2}\,\d{1,2}\,\d{1,2}(\,\d{6,11})*", row[1])
		if result is not None:
#			print result.group(0)
			text=result.group(0)
			list_param=text.split(',')
			if (len(list_param) == 5):
				fixedcid = list_param[4]
				print('fixedcid '+row[0]+' no default, and = '+list_param[4])
			else:
				fixedcid = fixedcid_def
				text=str(text)+','+str(fixedcid_def)
			list_number=list_param[0].split('-')
			cursor_sel=db.cursor()
			sel_sql="""SELECT * FROM findmefollow WHERE `grpnum`='%(num)s'"""%{"num":row[0]}
			cursor_sel.execute(sel_sql)
			row_sel=cursor_sel.fetchone()
			if row_sel is not None:
				for row_u in cursor_sel:
					grplist=''
					for row_number in list_number:
						result_number=re.match(r"^\d\d\d$", row_number)
						if result_number is not None:
							reshotka=''
						else:
							reshotka='#'
						if grplist == '':
							grplist=row_number+reshotka
						else:
							grplist=grplist+'-'+row_number+reshotka
#					print grplist
					check_fixedcid=subprocess.check_output('/usr/sbin/rasterisk -x "database show AMPUSER/'+row[0]+'/followme/fixedcid"',shell=True,universal_newlines=True)
					for line_fixedc in check_fixedcid.split('\n'):
						result_fixedcid=re.match(r"^/AMPUSER/", line_fixedc)
						if result_fixedcid is not None:
							line_fixedcid=line_fixedc.rstrip().split(': ')
							ad = str(row_u[4])+","+str(int(list_ring_strategy.index(str(row_u[1])))+1)+","+str(row_u[12])+","+str(row_u[2])+","+line_fixedcid[1]
							ad = re.sub('[#]', '', ad)
					if text != ad:
<<<<<<< HEAD
						file_log_followme=open(str(dir_conf)+'log/followme.log', 'a')
=======
						file_log_followme=open('/opt/asterisk/script/log/followme.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
						file_log_followme.write(str(date_time+"\t"+'У номера '+row[0]+' на сервере FreePBX было: '+ad+' заменили на '+text+"\n"))
						file_log_followme.close()
						upd_sql="""UPDATE findmefollow SET `strategy`='%(strat)s', `grptime`='%(grptime)s', `grplist`='%(grp)s', `pre_ring`='%(pre_ring)s' WHERE grpnum='%(num)s'"""%{"strat":list_ring_strategy[int(list_param[1])-1],"grptime":list_param[3],"grp":grplist,"num":row[0],"pre_ring":list_param[2]}
						upd_indb='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/'
						upd_zn=['changecid','ddial','fixedcid','grpconf','grplist','postdest','grptime','ringing','prering','strategy']
						subprocess.call(upd_indb+upd_zn[0]+' extern"', shell=True)
						subprocess.call(upd_indb+upd_zn[1]+' DIRECT"', shell=True)
						subprocess.call(upd_indb+upd_zn[2]+' '+fixedcid+'"', shell=True)
						subprocess.call(upd_indb+upd_zn[3]+' DISABLE"', shell=True)
						subprocess.call(upd_indb+upd_zn[4]+' '+grplist+'"', shell=True)
						subprocess.call(upd_indb+upd_zn[5]+' ext-local,'+row[0]+',dest"', shell=True)
						subprocess.call(upd_indb+upd_zn[6]+' '+list_param[3]+'"', shell=True)
						subprocess.call(upd_indb+upd_zn[7]+' Ring"', shell=True)
						subprocess.call(upd_indb+upd_zn[8]+' '+list_param[2]+'"', shell=True)
						subprocess.call(upd_indb+upd_zn[9]+' '+list_ring_strategy[int(list_param[1])-1]+'"', shell=True)
						cursor.execute(upd_sql)
						db.commit()
						restart=1
			else:
				grplist=''
				for row_number in list_number:
					result_number=re.match(r'^\d\d\d$', row_number)
					if result_number is not None:
						reshotka=''
					else:
						reshotka='#'
					if grplist == '':
						grplist=row_number+reshotka
					else:
						grplist=grplist+"-"+row_number+reshotka
				postdest="ext-local,"+row[0]+",dest"
<<<<<<< HEAD
				file_log_followme=open(str(dir_conf)+'log/followme.log', 'a')
=======
				file_log_followme=open('/opt/asterisk/script/log/followme.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
				file_log_followme.write(str(date_time+"\t"+'Для номера '+row[0]+' прописали переадресацию с параметрами: '+list_ring_strategy[int(list_param[1])-1]+','+list_param[3]+','+grplist+','+postdest+','+list_param[2]+"\n"))
				file_log_followme.close()
				ins_sql="""INSERT INTO findmefollow (grpnum,strategy,grptime,grppre,grplist,postdest,dring,rvolume,pre_ring,ringing,calendar_enable,calendar_match) VALUES ('%(grpnum)s','%(strat)s','%(grptime)s','','%(grpl)s','%(postd)s','','','%(pre_ring)s','Ring','0','yes')"""%{"grpnum":row[0],"strat":list_ring_strategy[int(list_param[1])-1],"grptime":list_param[3],"grpl":grplist,"postd":postdest,"pre_ring":list_param[2]}
				ins_str='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/'
				ins_zn=['changecid','fixedcid','grpconf','grplist','postdest','ddial','grptime','ringing','prering','strategy']
				subprocess.call(ins_str+ins_zn[0]+' extern"', shell=True)
				subprocess.call(ins_str+ins_zn[1]+' '+fixedcid+'"', shell=True)
				subprocess.call(ins_str+ins_zn[2]+' DISABLE"', shell=True)
				subprocess.call(ins_str+ins_zn[3]+' '+grplist+'"', shell=True)
				subprocess.call(ins_str+ins_zn[4]+' ext-local,'+row[0]+',dest"', shell=True)
				subprocess.call(ins_str+ins_zn[5]+' DIRECT"', shell=True)
				subprocess.call(ins_str+ins_zn[6]+' '+list_param[3]+'"', shell=True)
				subprocess.call(ins_str+ins_zn[7]+' Ring"', shell=True)
				subprocess.call(ins_str+ins_zn[8]+' '+list_param[2]+'"', shell=True)
				subprocess.call(ins_str+ins_zn[9]+' '+list_ring_strategy[int(list_param[1])-1]+'"', shell=True)
				cursor.execute(ins_sql)
				db.commit()
				restart=1
		else:
			print('У номера '+row[0]+' ошибка в строке '+row[1]);
#Off fw
#
	sql="SELECT userman_users.default_extension,userman_users.cell,findmefollow.grpnum from userman_users,findmefollow WHERE `cell` ='' AND `default_extension` !='none' AND userman_users.default_extension=findmefollow.grpnum"
	cursor.execute(sql)
	for row in cursor:
		if row[0]!='':
			restart=1
<<<<<<< HEAD
		file_log_followme=open(str(dir_conf)+'log/followme.log', 'a')
=======
		file_log_followme=open('/opt/asterisk/script/log/followme.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
		file_log_followme.write(str(date_time+"\t"+'В AD у номера '+row[0]+' удалили переадресацию'+"\n"))
		file_log_followme.close()
		del_sql="""DELETE FROM findmefollow WHERE `grpnum`='%(num)s'"""%{"num":row[0]}
		cursor.execute(del_sql)
		db.commit()
		upd_indb='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/changecid default"'
		upd_indb1='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/fixedcid "'
		upd_indb2='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/grplist '+row[0]+'"'
		upd_indb3='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/followme/ddial EXTENSION"'
		subprocess.call(upd_indb, shell=True)
		subprocess.call(upd_indb1, shell=True)
		subprocess.call(upd_indb2, shell=True)
		subprocess.call(upd_indb3, shell=True)

#Update names
#
sql="SELECT users.extension,users.name,userman_users.displayname FROM users,userman_users WHERE users.extension=userman_users.default_extension AND users.name!=userman_users.displayname"
cursor.execute(sql)
for row in cursor:
	if row[0]!='':
		restart=1
<<<<<<< HEAD
	file_log=open(str(dir_conf)+'log/rename.log', 'a')
=======
	file_log=open('/opt/asterisk/script/log/rename.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
	file_log.write(str(date_time + "\t" + ' У номера ' + "\t" + row[0] + ' изменился DN с ' + "\t" + row[1] + ' на ' + "\t" + row[2] + "\n"))
	file_log.close()
	spl=row[2].split()
	i=0
	names=''
	while i<len(spl):
		names=names+spl[i]+'\ '
		i=i+1
	in_indb='/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/cidname '+names[0:-2]+'"'
	subprocess.call(in_indb, shell=True)
	upd_sql="""UPDATE users,devices SET users.name='%(name)s',devices.description='%(name)s' WHERE users.extension=devices.id AND users.extension='%(num)s'"""%{"name":row[2],"num":row[0]}
	cal=row[2]+' <'+row[0]+'>'
	upd_sql1="""UPDATE sip SET data='%(callid)s' WHERE id='%(num)s' AND keyword='callerid'"""%{"callid":cal,"num":row[0]}
	cursor.execute(upd_sql)
	cursor.execute(upd_sql1)
	db.commit()

#Record check
#
sql="SELECT extension from users"
cursor.execute(sql)
for row in cursor:
	get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in external"'
	force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
	force_val=force.stdout.read()
	if force_val[7:12] != "force":
		restart=1
		subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/external force"',shell=True)
		subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/external force"',shell=True)
		subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/internal force"',shell=True)

#Check hung pjsip channels
check_calls=subprocess.check_output('/usr/sbin/rasterisk -x "pjsip show channels"',shell=True,universal_newlines=True)
line_calls=check_calls.split('\n')
for line_pjsip_calls in line_calls:
	result_calls=re.match(r'  Channel: PJSIP/', line_pjsip_calls)
	if result_calls is not None:
		new_line_pjsip_calls = ' '.join(line_pjsip_calls.split())
		line_calls_time=new_line_pjsip_calls.split(' ')
		hour=line_calls_time[3].split(':')
		if int(hour[0]) >= 2:
			channel=line_calls_time[1].split('/')
<<<<<<< HEAD
			channel_request_hangup_log=open(str(dir_conf)+'log/channel_request_hangup.log', 'a')
=======
			channel_request_hangup_log=open('/opt/asterisk/script/log/channel_request_hangup.log', 'a')
>>>>>>> 7b9a04524250f2defe24a452dd62a2fe244343c1
			channel_request_hangup_log.write(str(date_time+"\t"+line_calls_time[1]+"\t"+line_calls_time[3]+"\n"))
			channel_request_hangup_log.close()
			subprocess.call('/usr/sbin/rasterisk -x "channel request hangup '+channel[0]+'/'+channel[1]+'"',shell=True)

#Reload check
sql="SELECT `value` FROM admin WHERE `variable`='need_reload'"
cursor.execute(sql)
results=cursor.fetchone()
if results[0]=="true":
	print('!6666666!')
	restart=1
db.close()

if restart==1:
	subprocess.call("sudo /usr/bin/alias runuser=/usr/sbin/runuser", shell=True)
	subprocess.call("sudo /var/lib/asterisk/bin/retrieve_conf", shell=True)
#	subprocess.call("fwconsole reload", shell=True)
	subprocess.call("sudo /var/lib/asterisk/bin/module_admin reload", shell=True)
