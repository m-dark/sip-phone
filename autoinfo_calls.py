#!/usr/bin/env python3.6
# pip install mysql-connector-python

import os
import re
import sys
import io
import asyncio
import panoramisk
from panoramisk.call_manager import CallManager
import time
from datetime import datetime
import mysql.connector
import subprocess
import logging
from urllib import request, parse
import ssl
import random

date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_conf = '/opt/asterisk/script/autoprovisioning/'
dir_log = '/opt/asterisk/script/log/'
dir_log_autoinfo = '/opt/asterisk/script/autoinfo/'
timeout = 25000

log = logging.getLogger("autoinfo")
fh = logging.FileHandler(dir_log+'autoinfo.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(name)s: %(message)s"))
log.addHandler(fh)
log.setLevel(logging.DEBUG)
log.info('Start')

manager_host='127.0.0.1'
manager_port='5038'
manager_user='username'
manager_secret='password'

async def originate(log_autoinfo,in_callerid,callerid,wav_file,number):
    date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
    date_time_start = datetime.now()
    random_id=random.randint(100000000000, 999999999999)
    code = 0
    result_number=re.match(r'(\d{5}$)', number)
    if result_number is None:
        chanel = 'Local/'+number+'@outbound-allroutes'
    else:
        chanel = 'Local/'+number+'@from-did-direct'
    callmanager = CallManager.from_config('/opt/asterisk/script/autoprovisioning/config.ini')
    await callmanager.connect()
    call = await callmanager.send_originate({
        'Action': 'Originate',
        'ActionID': 'autoinfo-'+str(random_id),
#        'Channel': 'Local/'+number+'@outbound-allroutes',
#        'Channel': 'Local/'+number+'@from-did-direct',
        'Channel': chanel,
        'Exten': callerid,
        'Application': 'Playback',
        'Data': '/var/lib/asterisk/sounds/ru/custom/'+wav_file,
        'Context': 'all-allow-except-196XX',
        'Priority': '1',
        'Timeout': timeout,
        'CallerID': 'Auto Info <'+callerid+'>',
#        'Variable': 'SIPADDHEADER="Call-Info:\;answer-after=0"',
        'Async': 'true'})

    if call.queue.empty():
        code = 1
        print('Queue is EMPTY')
        date_time_end = datetime.now()
        date_diff = date_time_end - date_time_start
        print(str(date_time_start))
        print(str(date_time_end))
        print(str(date_diff)+'   '+str(date_diff.total_seconds()))
        if date_diff.total_seconds() < timeout/1000:
            print('-------------Абонент занят--------')
            file_log=open(str(dir_log_autoinfo)+log_autoinfo, 'a')
            file_log.write(str(date_time+';'+in_callerid+';'+callerid+';'+number+';'+wav_file+';'+'Абонент Занят'+"\n"))
            file_log.close()
        else:
            print('-------------Абонент не взял трубку--------')
            file_log=open(str(dir_log_autoinfo)+log_autoinfo, 'a')
            file_log.write(str(date_time+';'+in_callerid+';'+callerid+';'+number+';'+wav_file+';'+'Не взяли трубку'+"\n"))
            file_log.close()
    else:
        print(f'Queue size: {call.queue.qsize()}')

    while not call.queue.empty():
        print(f'Iterate queue, queue size: {call.queue.qsize()}')
        event = call.queue.get_nowait()
#        print(event)
        event_store = event.items()
        for event_one in event_store:
            print(event_one[0]+' : '+event_one[1])
        print('-----------------------------------------------------2')

    print(code)
    if code == 0:
        while True:
            try:
                event = await asyncio.wait_for(call.queue.get(), timeout=10.0)
                event_store = event.items()
                for event_one in event_store:
                    print(event_one[0]+' : '+event_one[1])
                print('-----------------------------------------------------3'+str(event.cause)+' -- '+str(event.event.lower()))
                if event.event.lower() == 'hangup' and event.cause in ('0', '17'):
                    print('Сообщение прослушали!')
                    file_log=open(str(dir_log_autoinfo)+log_autoinfo, 'a')
                    file_log.write(str(date_time+';'+in_callerid+';'+callerid+';'+number+';'+wav_file+';'+'Прослушали'+"\n"))
                    file_log.close()
                    break
                elif event.event.lower() == 'hangup' and event.cause in ('16'):
                    print('Сообщение не дослушали!')
                    file_log=open(str(dir_log_autoinfo)+log_autoinfo, 'a')
                    file_log.write(str(date_time+';'+in_callerid+';'+callerid+';'+number+';'+wav_file+';'+'Не дослушали'+"\n"))
                    file_log.close()
                    break
            except asyncio.TimeoutError:
                print('timeout!')
                break
    callmanager.clean_originate(call)
    callmanager.close()

def main():
    loop = asyncio.get_event_loop()
    log_autoinfo = sys.argv[1]
    in_callerid = sys.argv[2]
    callerid = sys.argv[3]
    wav_file = sys.argv[4]
    numbers = sys.argv[5]
    numbers = re.sub('[-]', '', numbers)
    numbers = re.sub('[ ]', '', numbers)
    numbers = re.sub('[(]', '', numbers)
    numbers = re.sub('[)]', '', numbers)
    result_numbers=re.search(r',', numbers)
    if result_numbers is None:
        result_number=re.match(r'((\d{5}$)|([23]\d{6}$)|(8[3489]\d{9}$))', numbers)
        if result_number is None:
            log.error('Номер может быть "XXXXX", "[23]XXXXXX" или "8[3489]XXXXXXXXX": '+numbers)
            print('Ошибка, номер может быть "XXXXX", "[23]XXXXXX" или "8[3489]XXXXXXXXX": '+numbers)
            sys.exit()
        else:
            log.info('Задание с номера: '+in_callerid+' Исходящий вызов с номера: '+callerid+' На номер: '+numbers+' Восспроизводим файл: '+wav_file)
            loop.run_until_complete(originate(log_autoinfo,in_callerid,callerid,wav_file,numbers))
    else:
        array_numbers = numbers.split(",")
        for number in array_numbers:
            result_number=re.match(r'((\d{5}$)|([23]\d{6}$)|(8[3489]\d{9}$))', number)
            if result_number is None:
                log.error('Номер может быть "XXXXX", "[23]XXXXXX" или "8[3489]XXXXXXXXX": '+number)
                print('Ошибка номер может быть "XXXXX", "[23]XXXXXX" или "8[3489]XXXXXXXXX": '+number)
            else:
                log.info('Задание с номера: '+in_callerid+' Исходящий вызов с номера: '+callerid+' На номер: '+number+' Восспроизводим файл: '+wav_file)
                loop.run_until_complete(originate(log_autoinfo,in_callerid,callerid,wav_file,number))
    loop.close()

if __name__ == '__main__':
    main()
