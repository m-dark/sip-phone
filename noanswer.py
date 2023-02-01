# -*- coding: utf-8 -*-
#кодировка
import sys
import os
import re
import smtplib
import email.message
server = smtplib.SMTP('smtp.gmail.com:587')
reload(sys)
sys.setdefaultencoding('utf-8')
import MySQLdb
import subprocess
from datetime import datetime
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/autoprovisioning/'
dir_log = '/opt/asterisk/script/log/'

fixedcid_def = ''
fw_auto = 0
aggregate_mwi = 0
call_waiting_yes = 0
secret = 0
secret_cisco_model_i = []
model = ''
call_waiting_i = []
recording_i = []
force_rport_yes = 0
force_rport_model_i = []
custom_context_default = 'from-internal'
dict_custom_context = dict()
ad_delete_extension = 0
dict_no_delete_extension = dict()
passwordemailreport = ''
sendto = ''

def sql_update(keyword, data, number, model):
	file_log=open(str(dir_log)+'cisco_update.log', 'a')
	file_log.write(str(date_time + "\t" + 'У номера' + "\t" + number + "\t" + 'был переключен параметр' + "\t" + keyword + "\t" + 'в' + "\t" + data + "\t" + 'так как модель телефона в AD' + "\t" + model +"\n"))
	file_log.close()
	upd_data_sql="""UPDATE sip SET data='%(new_data)s' WHERE keyword = '%(keyword)s' AND id='%(num)s'"""%{"new_data":data,"keyword":keyword,"num":number}
	cursor.execute(upd_data_sql)
	db.commit()

freepbx_pass = open (str(dir_conf)+'freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	#custom_context
	#custom_context = 19600-19699:governor; 19600-19699:errr
	result_line=re.match(r'passwordemailreport = ', line)
	if result_line is not None:
		param_passwordemailreport=line.split(' = ')
		passwordemailreport=param_passwordemailreport[1]
	result_line=re.match(r'sendto = ', line)
	if result_line is not None:
		param_sendto=line.split(' = ')
		sendto=param_sendto[1]
	result_line=re.match(r'custom_context = ', line)
	if result_line is not None:
		param_custom_context=line.split(' = ')
		custom_context_array=param_custom_context[1].split(':')
		result_custom_context=re.search('-', custom_context_array[0])
		if result_custom_context is not None:
			param_custom_context_num=custom_context_array[0].split('-')
			while int(param_custom_context_num[0]) <= int(param_custom_context_num[1]):
				dict_custom_context[int(param_custom_context_num[0])] = custom_context_array[1]
				param_custom_context_num[0]=int(param_custom_context_num[0])+1
		else:
			dict_custom_context[int(custom_context_array[0])] = custom_context_array[1]

	result_line=re.match(r'custom_context_default = ', line)
	if result_line is not None:
		param_custom_context_default=line.split(' = ')
		custom_context_default=param_custom_context_default[1]
	result_line=re.match(r'fixedcid = \d+', line)
	if result_line is not None:
		param_fixedcid=line.split(' = ')
		fixedcid_def=param_fixedcid[1]
	result_line=re.match(r'ad_delete_extension = \d', line)
	if result_line is not None:
		param_ad_delete_extension=line.split(' = ')
		ad_delete_extension=param_ad_delete_extension[1]
		
	result_line=re.match(r'no_delete_extension = \d', line)
	if result_line is not None:
		param_no_delete_extension=line.split(' = ')
		numper_no_delete_extension=param_no_delete_extension[1].split(',')
		for number in numper_no_delete_extension:
			result_line=re.search(r'-', number)
			if result_line is not None:
				start_end_number=number.split('-')
				if int(start_end_number[0]) < int(start_end_number[1]):
					while int(start_end_number[0]) <= int(start_end_number[1]):
						dict_no_delete_extension[int(start_end_number[0])] = 1
						start_end_number[0] = int(start_end_number[0]) + 1
			else:
				dict_no_delete_extension[int(number)] = 1

	result_line=re.match(r'fw_auto = \d', line)
	if result_line is not None:
		param_fw_auto=line.split(' = ')
		fw_auto=param_fw_auto[1]
	result_line=re.match(r'call_waiting_yes = \d+', line)
	if result_line is not None:
		param_call_waiting_yes=line.split(' = ')
		call_waiting_yes=param_call_waiting_yes[1]
	result_line=re.match(r'secret = \d', line)
	if result_line is not None:
		param_secret=line.split(' = ')
		secret=param_secret[1]
	result_line=re.match(r'secret_cisco = ', line)
	if result_line is not None:
		secret_cisco = line.split(' = ')
		secret_cisco_model = secret_cisco[1]
		result_line=re.search(',', secret_cisco_model)
		if result_line is not None:
			secret_cisco_model_i=secret_cisco_model.split(',')
		else:
			secret_cisco_model_i.append(secret_cisco_model)
	result_line=re.match(r'force_rport_yes = \d', line)
	if result_line is not None:
		param_force_rport_yes=line.split(' = ')
		force_rport_yes=param_force_rport_yes[1]
	result_line=re.match(r'force_rport_model = ', line)
	if result_line is not None:
		force_rport_model = line.split(' = ')
		force_rport_model_model = force_rport_model[1]
		result_line=re.search(',', force_rport_model_model)
		if result_line is not None:
			force_rport_model_i=force_rport_model_model.split(',')
		else:
			force_rport_model_i.append(force_rport_model_model)
	result_line=re.match(r'call_waiting_invisible = \d+', line)
	if result_line is not None:
		param_call_waiting_invisible=line.split(' = ')
		call_waiting_invisible=param_call_waiting_invisible[1]
		result_line=re.match(r'\d+,', call_waiting_invisible)
		if result_line is not None:
			call_waiting_i=call_waiting_invisible.split(',')
		else:
			call_waiting_i.append(call_waiting_invisible)
	result_line=re.match(r'recording = \d+', line)
	if result_line is not None:
		param_recording=line.split(' = ')
		recording=param_recording[1]
		result_line=re.match(r'\d+,', recording)
		if result_line is not None:
			recording_i=recording.split(',')
		else:
			recording_i.append(recording)
	result_line=re.match(r'aggregate_mwi = \d', line)
	if result_line is not None:
		param_aggregate_mwi=line.split(' = ')
		aggregate_mwi=param_aggregate_mwi[1]
freepbx_pass.close()

list_ring_strategy = ['ringallv2','ringallv2-prim','ringall','ringall-prim','hunt','hunt-prim','memoryhunt-prim','firstavailable','firstnotonphone']
db = MySQLdb.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor = db.cursor()
restart = 0
sendmail = 0
email_content2 = ''

#Если = 1, то на номерах которые создаются на FreePBX и не прописаны в файле freepbx.pass в переменной call_waiting_invisible= включется фишка: "Оставайтесь на линии абонент занят" (предварительно необходимо еще дополнительное назначение my-call-hold)
if call_waiting_yes == '1':
#Call Waiting
	check_cw=subprocess.check_output('/usr/sbin/rasterisk -x "database show CW"',shell=True,universal_newlines=True)
	line_cw=check_cw.split('\n')

# подумать над включением Ожидание звонка на номерах из файла.
# EKB
#ine_cw.remove('/CW/10301                                         : ENABLED                  ')

	for line_enable_cw in line_cw:
		call_waiting_enabled_yes = 0
#		result_cw=re.match(r'/CW/\d+', line_enable_cw)
		result_cw=re.search(r'ENABLED', line_enable_cw)
		if result_cw is not None:
			new_line_enable_cw = line_enable_cw.split(' ')
			new_line_enable_cw = new_line_enable_cw[0].split('/CW/')
			for no_call_waiting in call_waiting_i:
				if new_line_enable_cw[1] == no_call_waiting:
					call_waiting_enabled_yes = 1
			if call_waiting_enabled_yes == 0:
#				upd_cwdb='/usr/sbin/rasterisk -x "database put CW '+new_line_enable_cw[1]+' DISABLED'
				upd_cwdb='/usr/sbin/rasterisk -x "database del CW '+new_line_enable_cw[1]
				subprocess.call(upd_cwdb+'"', shell=True)
				restart=1
				file_log_cw=open(str(dir_log)+'busy_dest.log', 'a')
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
#			upd_busy_dest_sql="""UPDATE users,devices SET users.name='%(name)s',devices.description='%(name)s' WHERE users.extension=devices.id AND users.extension='%(num)s'"""%{"name":row[2],"num":row[0]}
			upd_busy_dest_sql="""UPDATE users SET users.busy_dest='%(b_dest)s' WHERE users.extension='%(num)s'"""%{"b_dest":'my-call-hold,s,1',"num":row[0]}
			cursor.execute(upd_busy_dest_sql)
			db.commit()
			restart=1
			file_log_busy_dest=open(str(dir_log)+'busy_dest.log', 'a')
			file_log_busy_dest.write(str(date_time+"\t"+'Для номера '+row[0]+' в Расширенных настройках включили при BUSY дополнительное назначение my-call-hold'+"\n"))
			file_log_busy_dest.close()
	db.commit()
#Call Waiting END

#Удаляем номер телефона с FreePBX если в AD номер был удален
if ad_delete_extension == "1":
	ad_delete_extension_sql="SELECT users.extension FROM users WHERE users.extension not in (SELECT default_extension FROM userman_users)"
	cursor.execute(ad_delete_extension_sql)
	for row in cursor:
		result=re.match(r"^9", row[0])
		if result is not None:
			print("Номер не удаляем: "+row[0])
		else:
			if int(row[0]) in dict_no_delete_extension:
				print('Номер '+str(row[0])+' нельзя удалять, так как он прописан в файле freepbx.pass')
			else:
				print(row[0])
				file_log=open(str(dir_log)+'ad_delete.log', 'a')
				file_log.write(str(date_time + "\t" + 'Был удалён номер ' + row[0] + ' с FreePBX, так как он был удален в AD'+"\n"))
				file_log.close()
				del_sip_ad_delete_extension_sql="""DELETE FROM sip WHERE `id`='%(extension)s'"""%{"extension":row[0]}
				cursor.execute(del_sip_ad_delete_extension_sql)
				del_ad_delete_extension_sql="""DELETE FROM users WHERE `extension`='%(extension)s'"""%{"extension":row[0]}
				cursor.execute(del_ad_delete_extension_sql)
				del_fw_ad_delete_extension_sql="""DELETE FROM findmefollow WHERE `grpnum`='%(extension)s'"""%{"extension":row[0]}
				cursor.execute(del_fw_ad_delete_extension_sql)
				del_devices_ad_delete_extension_sql="""DELETE FROM devices WHERE `id`='%(extension)s'"""%{"extension":row[0]}
				cursor.execute(del_devices_ad_delete_extension_sql)
				restart=1
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree AMPUSER/'+row[0]+'"',shell=True,universal_newlines=True)
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree DEVICE/'+row[0]+'"',shell=True,universal_newlines=True)
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree CALLTRACE/'+row[0]+'"',shell=True,universal_newlines=True)
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree CW/'+row[0]+'"',shell=True,universal_newlines=True)
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree CustomDevstate/FOLLOWME'+row[0]+'"',shell=True,universal_newlines=True)
				subprocess.check_output('/usr/sbin/rasterisk -x "database deltree CustomPresence/'+row[0]+'"',shell=True,universal_newlines=True)
	db.commit()

#FW
#
if fw_auto == "1":
	sql="SELECT default_extension,cell,displayname from userman_users WHERE `cell` !='' AND `default_extension` !='none' ORDER BY default_extension"
	cursor.execute(sql)
	for row in cursor:
		result=re.match(r"^(\d+(-\d+)*),\d{1,2}\,\d{1,2}\,\d{1,2}(\,\d{6,11})*", row[1])
		if result is not None:
			email_content2 = email_content2 + "<tr><td>"+row[0]+"</td><td>"+row[1]+"</td><td>"+row[2]+"</td></tr>"

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
						file_log_followme=open(str(dir_log)+'followme.log', 'a')
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
						sendmail=1
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
				file_log_followme=open(str(dir_log)+'followme.log', 'a')
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
				sendmail=1
		else:
			print('У номера '+row[0]+' ошибка в строке '+row[1]);
# Off fw
#
	sql="SELECT userman_users.default_extension,userman_users.cell,findmefollow.grpnum from userman_users,findmefollow WHERE `cell` ='' AND `default_extension` !='none' AND userman_users.default_extension=findmefollow.grpnum"
	cursor.execute(sql)
	for row in cursor:
		if row[0]!='':
			restart=1
			sendmail=1
		file_log_followme=open(str(dir_log)+'followme.log', 'a')
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
#FW end
	if sendmail == 1:
		email_content1 = """
<html>

<head> 
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 

<title>Отчет по номерам с настроенной переадресацией</title> 
<style type="text/css"> 
a {color: #d80a3e;} 
body, #header h1, #header h2, p {margin: 0; padding: 0;} 
#main {border: 1px solid #cfcece;} 
img {display: block;} 
#top-message p, #bottom p {color: #3f4042; font-size: 12px; font-family: Arial, Helvetica, sans-serif; } 
#header h1 {color: #ffffff !important; font-family: "Lucida Grande", sans-serif; font-size: 24px; margin-bottom: 0!important; padding-bottom: 0; } 
#header p {color: #ffffff !important; font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif; font-size: 12px; } 
h5 {margin: 0 0 0.8em 0;} 
h5 {font-size: 18px; color: #444444 !important; font-family: Arial, Helvetica, sans-serif; } 
p {font-size: 12px; color: #444444 !important; font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif; line-height: 1.5;} 
</style> 
</head> 

<body> 

<table width="100%" cellpadding="0" cellspacing="0" bgcolor="e4e4e4">
<tr>
<td> 
    <table id="main" width="800" align="center" cellpadding="0" cellspacing="15" bgcolor="ffffff"> 
	<tr> 
	    <td> 
		<table id="header" cellpadding="10" cellspacing="0" align="center" bgcolor="8fb3e9"> 
		    <tr> 
			<td width="570" align="center" bgcolor="#d80a3e"><h1>Переадресация настроена на номерах:</h1></td> 
		    </tr> 
		</table> 
	    </td> 
	</tr> 

	<tr> 
	    <td> 
		<table id="content-4" cellpadding="0" cellspacing="0" align="center" border="1px" solid="#cfcece"> 
		<thead>
		    <tr>
			<th width="140">Внутренний номер </th>
			<th width="200">Правило переадресации </th>
			<th width="240">Сотрудник </th>
		    </tr>
		</thead>
"""
#		email_content2 = """
#		    <tr>
#			<td>666</td>
#			<td>9999999999999999</td>
#			<td>kas</td>
#		    </tr>
#		    <tr>
#			<td>666</td>
#			<td>9999999999999999,34, 343 34</td>
#			<td>Павлеченко Ефстигней Макарович</td>
#		    </tr>
#"""
		email_content3 = """
		</table> 
	    </td> 
	</tr> 
</table> 
</td></tr></table><!-- wrapper --> 

</body> 
</html>
"""

		email_content = email_content1 + email_content2 + email_content3
		msg = email.message.Message()
		msg['Subject'] = 'Отчет по номерам с настроенной переадресацией'
		msg['From'] = 'report.freepbx@gmail.com'
		msg['To'] = sendto
		msg.add_header('Content-Type', 'text/html')
		msg.set_payload(email_content)
		s = smtplib.SMTP('smtp.gmail.com: 587')
		s.starttls()
		# Login Credentials for sending the mail 
		s.login(msg['From'], passwordemailreport)
		s.sendmail(msg['From'], [msg['To']], msg.as_string())

#Меняем пароль для sip-учетки номера (например cisco 7911 не переваривает пароль длинее 31, а во FreePBX длина по умолчанию 32)
#Update password sip
if secret == '1':
	for model in secret_cisco_model_i:
		model_sql="""SELECT sip.id, sip.data FROM userman_users, sip WHERE userman_users.home = '%(cisco)s' AND keyword = 'secret' AND userman_users.default_extension = sip.id AND CHAR_LENGTH(sip.data) > '30'"""%{"cisco":model}
		cursor.execute(model_sql)
		for row in cursor:
			if row[0] != '':
				restart=1
				new_pass = row[1][0:30]
				file_log=open(str(dir_log)+'new_pass.log', 'a')
				file_log.write(str(date_time + "\t" + 'У номера ' + row[0] + ' изменили пароль с' + "\t" + row[1] + "\t" + 'на' + "\t" + new_pass + "\t" + 'так как модель телефона в AD' + "\t" + model +"\n"))
				file_log.close()
				upd_pass_sql="""UPDATE sip SET data='%(new_pass)s' WHERE keyword = 'secret' AND id='%(num)s'"""%{"new_pass":new_pass,"num":row[0]}
				cursor.execute(upd_pass_sql)
		db.commit()

#Update password sip end#

#force_rport_yes = 0
#force_rport_model_i = []
#Включаем rewrite_contact и force_rport
if force_rport_yes == '1':
	force_rport_sql="SELECT default_extension, home FROM userman_users"
	cursor.execute(force_rport_sql)
	for row in cursor:
		check = 0
		for upd_force_rport in force_rport_model_i:
			if row[1] == upd_force_rport:
				check = 1
		rewrite_contact_sql = """SELECT id, data FROM sip WHERE keyword = 'rewrite_contact' AND id = '%(num)s'"""%{"num":row[0]}
		cursor.execute(rewrite_contact_sql)
		for no_yes in cursor:
			if str(no_yes[1]) == 'no':
				if check != 1:
					sql_update('rewrite_contact', 'yes', str(row[0]), str(row[1]))
					restart=1
			elif str(no_yes[1]) == 'yes':
				if check == 1:
					sql_update('rewrite_contact', 'no', str(row[0]), str(row[1]))
					restart=1
		force_rport_yes_no_sql = """SELECT id, data FROM sip WHERE keyword = 'force_rport' AND id = '%(num)s'"""%{"num":row[0]}
		cursor.execute(force_rport_yes_no_sql)
		for no_yes in cursor:
			if str(no_yes[1]) == 'no':
				if check != 1:
					sql_update('force_rport', 'yes', str(row[0]), str(row[1]))
					restart=1
			elif str(no_yes[1]) == 'yes':
				if check == 1:
					sql_update('force_rport', 'no', str(row[0]), str(row[1]))
					restart=1
	db.commit()

#Update names
#
sql="SELECT users.extension,users.name,userman_users.displayname FROM users,userman_users WHERE users.extension=userman_users.default_extension AND users.name!=userman_users.displayname"
cursor.execute(sql)
for row in cursor:
	if row[0]!='':
		restart=1
	file_log=open(str(dir_log)+'rename.log', 'a')
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
#recording_i
sql="SELECT extension from users"
cursor.execute(sql)
for row in cursor:
	not_recording = 0
	for number_recording in recording_i:
		if row[0] == number_recording:
			not_recording = 1
	if not_recording == 1:
		print(number_recording)
#Контроль внешних входящих соединений
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in external"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:12] != "never":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/external never"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внешних входящих соединений переключили в состояние never'+"\n"))
#			file_log_no_recording.close()

#Контроль внешних исходящих соединений
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/out external"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:12] != "never":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/external never"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внешних исходящих соединений переключили в состояние never'+"\n"))
#			file_log_no_recording.close()

#Контроль внутренних входящих соединений
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in internal"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:12] != "never":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/internal never"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внутренних входящих соединений переключили в состояние never'+"\n"))
#			file_log_no_recording.close()

#Контроль внутренних исходящих соединений
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/out internal"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:12] != "never":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/internal never"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внутренних исходящих соединений переключили в состояние never'+"\n"))
#			file_log_no_recording.close()

#Запись разговоров с телефона через *1
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording ondemand"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:15] != "override":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/ondemand override"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' возможность включать выключать запись разговора через *1 переключили в состояние override'+"\n"))
#			file_log_no_recording.close()

#Приоритет политики использования записи разговоров
#		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording priority"'
#		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
#		force_val=force.stdout.read()
#		if force_val[7:9] != "10":
#			restart=1
#			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/priority 10"',shell=True)
#			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
#			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' Приоритет политики использования записи разговоров переключили в 10'+"\n"))
#			file_log_no_recording.close()
	else:
#Контроль внешних входящих соединений
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in external"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:12] != "force":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/external force"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внешних входящих соединений переключили в состояние force'+"\n"))
			file_log_no_recording.close()

#Контроль внешних исходящих соединений
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/out external"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:12] != "force":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/external force"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внешних исходящих соединений переключили в состояние force'+"\n"))
			file_log_no_recording.close()

#Контроль внутренних входящих соединений
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in internal"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:12] != "force":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/internal force"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внутренних входящих соединений переключили в состояние force'+"\n"))
			file_log_no_recording.close()

#Контроль внутренних исходящих соединений
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording/out internal"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:15] != "dontcare":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/internal dontcare"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' запись разговоров внутренних исходящих соединений переключили в состояние dontcare'+"\n"))
			file_log_no_recording.close()

#Запись разговоров с телефона через *1
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording ondemand"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:15] != "disabled":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/ondemand disabled"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' возможность включать выключать запись разговора через *1 переключили в состояние disabled'+"\n"))
			file_log_no_recording.close()

#Приоритет политики использования записи разговоров
		get_str='/usr/sbin/rasterisk -x "database get AMPUSER/'+row[0]+'/recording priority"'
		force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
		force_val=force.stdout.read()
		if force_val[7:9] != "10":
			restart=1
			subprocess.call('/usr/sbin/rasterisk -x "database put AMPUSER '+row[0]+'/recording/priority 10"',shell=True)
			file_log_no_recording=open(str(dir_log)+'no_recording.log', 'a')
			file_log_no_recording.write(str(date_time+"\t"+'На номере '+row[0]+' Приоритет политики использования записи разговоров переключили в 10'+"\n"))
			file_log_no_recording.close()

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
			channel_request_hangup_log=open(str(dir_log)+'channel_request_hangup.log', 'a')
			channel_request_hangup_log.write(str(date_time+"\t"+line_calls_time[1]+"\t"+line_calls_time[3]+"\n"))
			channel_request_hangup_log.close()
			subprocess.call('/usr/sbin/rasterisk -x "channel request hangup '+channel[0]+'/'+channel[1]+'"',shell=True)

#Включаем на всех номерах "Агрегированные MWI yes"
if aggregate_mwi == "1":
	sql="SELECT id FROM sip WHERE keyword = 'aggregate_mwi' and data = 'no'"
	cursor.execute(sql)
	for row in cursor:
		if row[0]!='':
			file_log=open(str(dir_log)+'aggregate_mwi.log', 'a')
			file_log.write(str(date_time + "\t" + ' На номере ' + "\t" + row[0] + ' Включили \"Агрегированные MWI\"' + "\n"))
			file_log.close()
			upd_sql="""UPDATE sip SET data='yes' WHERE id='%(num)s' AND keyword='aggregate_mwi'"""%{"num":row[0]}
			cursor.execute(upd_sql)
			db.commit()
			restart=1
elif aggregate_mwi == "2":
	sql="SELECT id FROM sip WHERE keyword = 'aggregate_mwi' and data = 'yes'"
	cursor.execute(sql)
	for row in cursor:
		if row[0]!='':
			file_log=open(str(dir_log)+'aggregate_mwi.log', 'a')
			file_log.write(str(date_time + "\t" + ' На номере ' + "\t" + row[0] + ' Вылючили \"Агрегированные MWI\"' + "\n"))
			file_log.close()
			upd_sql="""UPDATE sip SET data='no' WHERE id='%(num)s' AND keyword='aggregate_mwi'"""%{"num":row[0]}
			cursor.execute(upd_sql)
			db.commit()
			restart=1

#Прописываем Custom Context
#custom_context_default = all-allow-except-196XX
#custom_context = 19600-19699:governor
sql="SELECT sip.id, sip.keyword, sip.data, sip.flags FROM users, sip WHERE users.extension = sip.id AND sip.keyword = 'context'"
cursor.execute(sql)
for row in cursor:
	if dict_custom_context.get(int(row[0])) is None:
		if row[2] != custom_context_default:
##			print('Надо заменить'+row[0]+"\t"+row[2]+'!'+custom_context_default)
			upd_sql="""UPDATE sip SET data='%(custom_context_default)s', flags='45' WHERE id='%(num)s' AND keyword='context'"""%{"custom_context_default":custom_context_default, "num":row[0]}
			cursor.execute(upd_sql)
			db.commit()
			restart=1
	else:
		if row[2] != dict_custom_context[int(row[0])]:
##			print('!!Надо заменить'+row[0]+"\t"+row[2])
			upd_sql="""UPDATE sip SET data='%(custom_context)s', flags='45' WHERE id='%(num)s' AND keyword='context'"""%{"custom_context":dict_custom_context[int(row[0])], "num":row[0]}
			cursor.execute(upd_sql)
			db.commit()
			restart=1
	db.commit()

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
	subprocess.call("sudo /var/lib/asterisk/bin/fwconsole reload", shell=True)
