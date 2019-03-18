import sqlite3
import json
import datetime
import logging
import requests
from time import sleep
from threading import Thread
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import Flask, request, g
from flask_restful import Resource, Api
from gpiozero import Button, OutputDevice
from hx711 import HX711
import config
import bc_scanner

# Load config
conf = config.get_config()

# Setup scale amp
hx711 = HX711(
    dout_pin=conf['SCALE_DATA_PIN'],
    pd_sck_pin=conf['SCALE_CLOCK_PIN'],
    channel=conf['SCALE_CHANNEL'],
    gain=conf['SCALE_GAIN']
)

#Create objects for physical objects
lid_switch = Button(conf['LID_SWITCH_PIN)'])
lid_open_button = OutputDevice(conf['LID_OPEN_PIN'], active_high=False, initial_value=False)
lid_close_button = OutputDevice(conf['LID_CLOSE_PIN'], active_high=False, initial_value=False)
light = OutputDevice(conf['LIGHT_PIN'], active_high=False, initial_value=False)
fan = OutputDevice(conf['FAN_PIN'], active_high=False, initial_value=False)
led = OutputDevice(conf['LED_PIN'], active_high=False, initial_value=False)

#Setup parser

#Setup database
DATABASE = '/srv/trashcan/venv/database/database.db'

# Shared app context
app = Flask(__name__)
scheduler = APScheduler()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def start_api():
    # Config API
    my_api = Api(app)
    my_api.add_resource(Index, '/')
    my_api.add_resource(Api, '/api')
    my_api.add_resource(Lid, '/api/lid')
    my_api.add_resource(Scale, '/api/scale')
    my_api.add_resource(Light, '/api/light')
    my_api.add_resource(Fan, '/api/fan')
    my_api.add_resource(BarcodeList, '/api/barcode')
    my_api.add_resource(WeightList, '/api/weight')
    my_api.add_resource(Barcode, '/api/barcode/<barcode_id>')
    my_api.add_resource(Weight, '/api/weight/<weight_id>')
    my_api.add_resource(ConfigList, 'api/config')
    my_api.add_resource(ConfigItem, 'api/config/<option_name>')

    # Config scheduler
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()

    app.run()

# Watchdog to monitor db config table for changes
def start_change_monitor():
    change_id = config.get_last_change_id()
    while True:
        new_conf_id = config.get_last_change_id()
        if new_conf_id > change_id:
            config.get_config()
            change_id = new_conf_id
            # Restart scheduler with new values
            scheduler.shutdown()
            scheduler.start()
        sleep(config['WATCHDOG_TIMER'])

def start_barcode_scanner():
    while True:
        if lid_switch.is_active():
            bc_scanner.read()
        sleep(conf['BARCODE_SLEEP'])


# Scheduler
class Config:
    JOBS = [
        {'id' : 'long_cycle_uvc',
         'func' : 'app:job1',
         'trigger' : 'cron',
         'hour' : conf['long_cycle_uvc_minute'],
         'minute' : conf['long_cycle_uvc_minute']
        },
        {'id': 'short_cycle_uvc',
         'func': 'app:job2',
         'trigger': 'cron',
         'hour': conf['short_cycle_uvc_hour'],
         'minute': conf['short_cycle_uvc_minute']
        },
        {'id': 'long_cycle_fan',
         'func': 'app:job3',
         'trigger': 'cron',
         'hour': conf['long_cycle_fan_hour'],
         'minute': conf['long_cycle_fan_minute']
        },
        {'id': 'short_cycle_fan',
         'func': 'app:job4',
         'trigger': 'cron',
         'hour': conf['short_cycle_fan_hour'],
         'minute': conf['short_cycle_fan_minute',]
        },
        {'id': 'long_cycle_both',
         'func': 'app:job5',
         'trigger': 'cron',
         'hour': conf['long_cycle_both_hour'],
         'minute': conf['long_cycle_both_minute']
        },
        {'id': 'short_cycle_both',
         'func': 'app:job6',
         'trigger': 'cron',
         'hour': conf['short_cycle_both_hour'],
         'minute': conf['short_cycle_both_both',]
        },
        {'id' : 'phone_home',
         'func' : 'app:job7',
         'trigger' : 'interval',
         'seconds' : conf['phone_home_sleep']
        },
        {'id' : 'broadcast_location',
         'func' : 'app:job8',
         'trigger' : 'interval',
         'seconds' : conf['broadcast_sleep']
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

    # Short cycle UVC
    def job2(self):
        if requests.get('http://127.0.0.1/api/light').text == 'on':
            logging.warning("Light already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/light?action=on'))
        sleep(config['SHORT_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/light?action=off'))


    # Long cycle fan
    def job3(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        sleep(config['LONG_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))

    # Short cycle fan
    def job4(self):
        if requests.get('http://127.0.0.1/api/fan').text == 'on':
            logging.warning("Fan already on")
            return
        responses = list()
        responses.append(requests.put('http://127.0.0.1/api/fan?action=on'))
        sleep(config['SHORT_CYCLE_SLEEP'])
        responses.append(requests.put('http://127.0.0.1/api/fan?action=off'))

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

    # Phone home to AWS server
    def job7(self):
        #TODO write this
        logging.debug('Phoned home to server')
        return

    # Broadcast location to wi-fi
    def job8(self):
        #TODO write this too
        logging.debug('Broadcast location')
        return

class Index (Resource):
    def get(self):
        content = "<h1>This is an index page</h1>"
        return content

class Api(Resource):
    def get(self):
        content = "<h1>This is an API page</h1>"
        return content

class Lid(Resource):
    def get(self):
        if lid_switch.value:
            status = 'open'
        else:
            status = 'closed'
        return status
    def put(self):
        action = request.args.get('action')

        if action == 'off':
            lid_close_button.on()
            logging.info('Lid closed')
        elif action == 'on':
            lid_open_button.on()
            logging.info('Lid opened')
        elif action == 'toggle':
            if lid_switch.value:
                lid_close_button.on()
                logging.info('Lid closed')
            else:
                lid_open_button.on()
                logging.info('Lid opened')
        else:
            return 400
        return 'Success'

class Light(Resource):
    def get(self):
        if light.value:
            status = 'off'
        else:
            status = 'on'
        return status

    def put(self):
        action = request.args.get('action')

        if action == 'off':
            light.off()
        elif action == 'on':
            light.on()
        elif action == 'toggle':
            light.toggle()
        else:
            return 400
        return 'Success'

class Fan(Resource):
    def get(self):
        if fan.value:
            status = 'off'
        else:
            status = 'on'
        return status

    def put(self):
        action = request.args.get('action')

        if action == 'off':
            fan.off()
        elif action == 'on':
            fan.on()
        elif action == 'toggle':
            fan.toggle()
        else:
            return 400
        return 'Success'


class LightED(Resource):
    def get(self):
            if led.value:
                status = 'on'
            else:
                status = 'off'
            return status

    def put(self):
        action = request.args.get('action')

        if action == 'off':
            led.off()
        elif action == 'on':
            led.on()
        elif action == 'toggle':
            led.toggle()
        else:
            return 400
        return 'Success'

class Scale (Resource):
    def get(self):
        hx711.reset() #Maybe not necessary
        results = hx711.get_raw_data(conf['NUM_MEASUREMENTS'])
        return sum(results)/len(results) - conf['TARE']

    def put(self):
        hx711.reset()  # Maybe not necessary
        config.store_config('TARE',hx711.get_raw_data(conf['NUM_MEASUREMENTS']))
        return 'Success'

class WeightList (Resource):
    def get(self):
        conn = get_db()
        conn.cursor().execute("SELECT * FROM[Weight]")
        results = conn.cursor().fetchall()
        return json.dumps(results)

    def delete(self):
        return 501

class BarcodeList (Resource):
    def get(self):
        conn = get_db()
        conn.cursor().execute("SELECT * FROM[Barcode]")
        results = conn.cursor().fetchall()
        return json.dumps(results)

    def delete(self):
        return 501

class Barcode (Resource):
    def post(self,barcode_id):
        conn = get_db()
        time = datetime.datetime.now()
        barcode = request.args.get('barcode')
        conn.cursor().execute("INSERT INTO Barcode ([barcode_id],[timestamp],[barcode]) VALUES(?, ?, ?)",(barcode_id,time,barcode,))
        conn.commit()
        return barcode_id

    def delete(self, barcode_id):
        conn = get_db()
        result = conn.cursor().execute("DELETE FROM[Barcode] WHERE barcode_id = ?",(barcode_id,))
        conn.commit()
        return result


class Weight (Resource):
    def post(self,weight_id):
        conn = get_db()
        time = datetime.datetime.now()
        weight = request.args.get('weight')
        conn.cursor().execute("INSERT INTO Weight ([weight_id],[timestamp],[weight]) VALUES(?, ?, ?)",(weight_id,time,weight,))
        conn.commit()
        return weight_id

    def delete(self, weight_id):
        conn = get_db()
        result = conn.cursor().execute("DELETE FROM[Weight] WHERE weight_id = ?",(weight_id,))
        conn.commit()
        return result

class ConfigList (Resource):
    def get(self):
        return json.dumps(conf)

class ConfigItem (Resource):
    def get(self, option_name):
        return json.dumps(conf[option_name])

    def put(self, option_name):
        value = request.args.get('value')
        config.store_config(option_name,value)

    def post(self, option_name):
        value = request.args.get('value')
        config.store_config(option_name,value)

    def delete(self, option_name):
        config.delete_config(option_name)



if __name__ == '__main__':
    t1 = Thread(target = start_api())
    t2 = Thread(target = start_change_monitor())
    t3 = Thread(target = bc_scanner.run())

    t1.start()
    t2.start()
    t3.start()

