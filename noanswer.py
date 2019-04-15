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
dir_conf = '/etc/asterisk/script/';
freepbx_pass = open (str(dir_conf)+'freepbx.pass','r')
for line in (line.rstrip() for line in freepbx_pass.readlines()):
	result_line=re.match(r'(fixedcid = \d+)', line)
	if result_line is not None:
		param_fixedcid=line.split(' = ')
		fixedcid_def=param_fixedcid[1]
freepbx_pass.close()
list_ring_strategy = ['ringallv2','ringallv2-prim','ringall','ringall-prim','hunt','hunt-prim','memoryhunt-prim','firstavailable','firstnotonphone']
db = MySQLdb.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor = db.cursor()
restart=0
#FW
#
sql="SELECT default_extension,cell from userman_users WHERE `cell` !='' AND `default_extension` !='none'"
cursor.execute(sql)
for row in cursor:
	result=re.match(r'((\d+(-\d+)*),\d\,\d+\,\d+)', row[1])
	if result is not None:
#		print result.group(0)
		text=result.group(0)
		list_param=text.split(',')
		if (len(list_param) == 5):
			fixedcid = list_param[4]
			print("fixedcid")
		else:
			fixedcid = fixedcid_def
		list_number=list_param[0].split('-')
		cursor_sel=db.cursor()
		sel_sql="""SELECT * FROM findmefollow WHERE `grpnum`='%(num)s'"""%{"num":row[0]}
		cursor_sel.execute(sel_sql)
		row_sel=cursor_sel.fetchone()
		if row_sel is not None:
			for row_u in cursor_sel:
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
#				print grplist
				ad = str(row_u[4])+","+str(int(list_ring_strategy.index(str(row_u[1])))+1)+","+str(row_u[12])+","+str(row_u[2])
				ad = re.sub('[#]', '', ad)
				if text != ad:
					upd_sql="""UPDATE findmefollow SET `strategy`='%(strat)s', `grptime`='%(grptime)s', `grplist`='%(grp)s', `pre_ring`='%(pre_ring)s' WHERE grpnum='%(num)s'"""%{"strat":list_ring_strategy[int(list_param[1])-1],"grptime":list_param[3],"grp":grplist,"num":row[0],"pre_ring":list_param[2]}
					upd_indb='rasterisk -x "database put AMPUSER '+row[0]+'/followme/'
					upd_zn=['changecid','fixedcid','grpconf','grplist','postdest','ddial','grptime','ringing','prering','strategy']
					subprocess.call(upd_indb+upd_zn[0]+' extern"', shell=True)
					subprocess.call(upd_indb+upd_zn[1]+' '+fixedcid+'"', shell=True)
					subprocess.call(upd_indb+upd_zn[2]+' DISABLE"', shell=True)
					subprocess.call(upd_indb+upd_zn[3]+' '+grplist+'"', shell=True)
					subprocess.call(upd_indb+upd_zn[4]+' ext-local,'+row[0]+',dest"', shell=True)
					subprocess.call(upd_indb+upd_zn[5]+' DIRECT"', shell=True)
					subprocess.call(upd_indb+upd_zn[6]+' '+list_param[3]+'"', shell=True)
					subprocess.call(upd_indb+upd_zn[7]+' Ring"', shell=True)
					subprocess.call(upd_indb+upd_zn[8]+' '+list_param[2]+'"', shell=True)
					subprocess.call(upd_indb+upd_zn[9]+' '+list_ring_strategy[int(list_param[1])-1]+'"', shell=True)
					cursor.execute(upd_sql)
					db.commit()
					restart=1
		else:
			print('!!!!!!!!!!')
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
			ins_sql="""INSERT INTO findmefollow (grpnum,strategy,grptime,grppre,grplist,postdest,dring,rvolume,pre_ring,ringing,calendar_enable,calendar_match) VALUES ('%(grpnum)s','%(strat)s','%(grptime)s','','%(grpl)s','%(postd)s','','','%(pre_ring)s','Ring','0','yes')"""%{"grpnum":row[0],"strat":list_ring_strategy[int(list_param[1])-1],"grptime":list_param[3],"grpl":grplist,"postd":postdest,"pre_ring":list_param[2]}
			ins_str='rasterisk -x "database put AMPUSER '+row[0]+'/followme/'
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
	del_sql="""DELETE FROM findmefollow WHERE `grpnum`='%(num)s'"""%{"num":row[0]}
	cursor.execute(del_sql)
	db.commit()
	upd_indb='rasterisk -x "database put AMPUSER '+row[0]+'/followme/changecid default"'
	upd_indb1='rasterisk -x "database put AMPUSER '+row[0]+'/followme/fixedcid "'
	upd_indb2='rasterisk -x "database put AMPUSER '+row[0]+'/followme/grplist '+row[0]+'"'
	upd_indb3='rasterisk -x "database put AMPUSER '+row[0]+'/followme/ddial EXTENSION"'
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
	file_log=open('/etc/asterisk/script/log/rename.log', 'a')
	file_log.write(str(date_time + "\t" + ' У номера ' + "\t" + row[0] + ' изменился DN с ' + "\t" + row[1] + ' на ' + "\t" + row[2] + "\n"))
	file_log.close()
	spl=row[2].split()
	i=0
	names=''
	while i<len(spl):
		names=names+spl[i]+'\ '
		i=i+1
	in_indb='rasterisk -x "database put AMPUSER '+row[0]+'/cidname '+names[0:-2]+'"'
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
	get_str='rasterisk -x "database get AMPUSER/'+row[0]+'/recording/in external"'
	force=subprocess.Popen(get_str, shell=True, stdout=subprocess.PIPE)
	force_val=force.stdout.read()
	if force_val[7:12] != "force":
		restart=1
		subprocess.call('rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/external force"',shell=True)
		subprocess.call('rasterisk -x "database put AMPUSER '+row[0]+'/recording/out/external force"',shell=True)
		subprocess.call('rasterisk -x "database put AMPUSER '+row[0]+'/recording/in/internal force"',shell=True)

#Reload check
sql="SELECT `value` FROM admin WHERE `variable`='need_reload'"
cursor.execute(sql)
results=cursor.fetchone()
if results[0]=="true":
	print(6666666)
        restart=1
db.close()

if restart==1:
	subprocess.call("alias runuser=/usr/sbin/runuser", shell=True)
	subprocess.call("/var/lib/asterisk/bin/retrieve_conf", shell=True)
#	subprocess.call("fwconsole reload", shell=True)
	subprocess.call("/var/lib/asterisk/bin/module_admin reload", shell=True)
