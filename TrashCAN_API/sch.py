import logging
import requests
import socket
import json
from time import sleep
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import config

# Scheduler
class Config:
    JOBS = [
        {'id' : 'long_cycle_uvc',
         'func' : 'app:job1',
         'trigger' : 'cron',
         'hour' : config.conf['long_cycle_uvc_minute'],
         'minute' : config.conf['long_cycle_uvc_minute']
        },
        {'id': 'short_cycle_uvc',
         'func': 'app:job2',
         'trigger': 'cron',
         'hour': config.conf['short_cycle_uvc_hour'],
         'minute': config.conf['short_cycle_uvc_minute']
        },
        {'id': 'long_cycle_fan',
         'func': 'app:job3',
         'trigger': 'cron',
         'hour': config.conf['long_cycle_fan_hour'],
         'minute': config.conf['long_cycle_fan_minute']
        },
        {'id': 'short_cycle_fan',
         'func': 'app:job4',
         'trigger': 'cron',
         'hour': config.conf['short_cycle_fan_hour'],
         'minute': config.conf['short_cycle_fan_minute',]
        },
        {'id': 'long_cycle_both',
         'func': 'app:job5',
         'trigger': 'cron',
         'hour': config.conf['long_cycle_both_hour'],
         'minute': config.conf['long_cycle_both_minute']
        },
        {'id': 'short_cycle_both',
         'func': 'app:job6',
         'trigger': 'cron',
         'hour': config.conf['short_cycle_both_hour'],
         'minute': config.conf['short_cycle_both_both',]
        },
        {'id' : 'phone_home',
         'func' : 'app:job7',
         'trigger' : 'interval',
         'seconds' : config.conf['phone_home_sleep']
        },
        {'id' : 'broadcast_location',
         'func' : 'app:job8',
         'trigger' : 'interval',
         'seconds' : config.conf['broadcast_sleep']
        }
    ]
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:////database/database.db')
    }
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 10}
    }
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': True,
        'max_instances': 1
    }
    SCHEDULER_API_ENABLED = True

    # Long cycle UVC
    def job1(self):
        if requests.get('http://127.0.0.1/api/light').text == 'on':
            logging.warning("Light already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/light?action=on'))
        sleep(config['LONG_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/light?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Short cycle UVC
    def job2(self):
        if requests.get('http://127.0.0.1/api/light').text == 'on':
            logging.warning("Light already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/light?action=on'))
        sleep(config['SHORT_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/light?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Long cycle fan
    def job3(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        sleep(config['LONG_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Short cycle fan
    def job4(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        sleep(config['SHORT_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Long cycle both
    def job5(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        if requests.get('http://127.0.0.1/api/light').text == 'on':
            logging.warning("Light already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        responses.append(requests.put('http://127.0.0.1/api/light?action=on'))
        sleep(config['LONG_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))
        responses.append(requests.put('http://127.0.0.1/api/light?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Short cycle both
    def job6(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        if requests.get('http://127.0.0.1/api/light').text == 'on':
            logging.warning("Light already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        responses.append(requests.put('http://127.0.0.1/api/light?action=on'))
        sleep(config['SHORT_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))
        responses.append(requests.put('http://127.0.0.1/api/light?action=off'))
        for index, response in responses:
            if response is not '200':
                logging.warning("Error from API: %s", responses[index])

    # Phone home to AWS server. Attempt to upload any stored barcodes and weight measurements.
    def job7(self):
        logging.debug('Phone home to server started')

        r = requests.get('http://127.0.0.1/api/weight')
        rjson = r.json()
        for line in rjson.items():
            fails = 0
            try:
                requests.post(config.conf['HOME_SERVER_URL']+'/anotherurl?weight='+line['weight'], timeout = 0.5)
                requests.delete('http://127.0.0.1/api/weight/'+line['weight_id'])
            except requests.exceptions as e:
                fails += 1
                logging.warning('Weight upload failed')
                if fails >= 3:
                    logging.error('Three failed uploads. Aborting weight upload')
                    break

        r = requests.get('http://127.0.0.1/api/barcode')
        rjson = r.json()
        for line in rjson.items():
            fails = 0
            try:
                requests.post(config.conf['HOME_SERVER_URL']+'/barcode-lookup?upc='+line['barcode'], timeout=0.5)
                requests.delete('http://127.0.0.1/api/weight/' + line['barcode_id'])
            except requests.exceptions as e:
                fails += 1
                logging.warning('Barcode upload failed')
                if fails >= config.conf['UPLOAD_FAILURE_LIMIT']:
                    logging.error(fails+' failed uploads. Aborting barcode upload')
                    break
        logging.debug('Phone home to server complete')

    # Broadcast location to wi-fi
    def job8(self):
        logging.debug('WiFi broadcast started.')
        msg = socket.gethostbyname(socket.gethostname())

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #Set timeout for blocking socket
        server.settimeout(0.2)
        server.bind("", 0) #0 binds to any available port

        server.sendto(msg, ('<broadcast>', config.conf['PI_BROADCAST_PORT']))

        logging.debug('WiFi broadcast location complete')
