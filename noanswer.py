# -*- coding: utf-8 -*-
#кодировка
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')
import MySQLdb
import subprocess
from datetime import datetime
date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
db = MySQLdb.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor = db.cursor()
restart=0
#FW
#
sql="SELECT default_extension,cell from userman_users WHERE `cell` !='' AND `default_extension` !='none'"
cursor.execute(sql)
for row in cursor:
	sel_sql="""SELECT * FROM findmefollow WHERE `grpnum`='%(num)s'"""%{"num":row[0]}
	cursor_sel=db.cursor()
	cursor_sel.execute(sel_sql)
	row_sel=cursor_sel.fetchone()
	if row_sel is not None:
		for row_u in cursor_sel:
			grplist=row[0]+"-"+row[1]+"#"
#			print grplist
			if grplist!=row_u[4]:
				upd_sql="""UPDATE findmefollow SET `grplist`='%(grp)s' WHERE grpnum='%(num)s'"""%{"grp":grplist,"num":row[0]}
				upd_indb='rasterisk -x "database put AMPUSER '+row[0]+'/followme/grplist '+grplist+'"'
				subprocess.call(upd_indb, shell=True)
				cursor.execute(upd_sql)
				db.commit()
				restart=1
	else:
		grplist=row[0]+"-"+row[1]+"#"
		postdest="ext-local,"+row[0]+",dest"
		ins_sql="""INSERT INTO findmefollow (grpnum,strategy,grptime,grppre,grplist,postdest,dring,rvolume,pre_ring,ringing,calendar_enable,calendar_match) VALUES ('%(grpnum)s','ringall','30','','%(grpl)s','%(postd)s','','','30','Ring','0','yes')"""%{"grpnum":row[0],"grpl":grplist,"postd":postdest}
		ins_str='rasterisk -x "database put AMPUSER '+row[0]+'/followme/'
		ins_zn=['grpconf','grplist','postdest','ddial','grptime','ringing','prering','strategy']
		subprocess.call(ins_str+ins_zn[0]+' DISABLE"', shell=True)
		subprocess.call(ins_str+ins_zn[1]+' '+grplist+'"', shell=True)
                subprocess.call(ins_str+ins_zn[2]+' ext-local,'+row[0]+',dest"', shell=True)
                subprocess.call(ins_str+ins_zn[3]+' DIRECT"', shell=True)
                subprocess.call(ins_str+ins_zn[4]+' 30"', shell=True)
                subprocess.call(ins_str+ins_zn[5]+' Ring"', shell=True)
                subprocess.call(ins_str+ins_zn[6]+' 30"', shell=True)
                subprocess.call(ins_str+ins_zn[7]+' ringall"', shell=True)
		cursor.execute(ins_sql)
		db.commit()
		restart=1


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
	upd_indb='rasterisk -x "database put AMPUSER '+row[0]+'/followme/grplist '+row[0]+'"'
	upd_indb1='rasterisk -x "database put AMPUSER '+row[0]+'/followme/ddial EXTENSION"'
	subprocess.call(upd_indb, shell=True)
	subprocess.call(upd_indb1, shell=True)

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
        restart=1


db.close()
if restart==1:
	subprocess.call("alias runuser=/usr/sbin/runuser", shell=True)
	subprocess.call("/var/lib/asterisk/bin/retrieve_conf", shell=True)
#	subprocess.call("fwconsole reload", shell=True)
	subprocess.call("/var/lib/asterisk/bin/module_admin reload", shell=True)
