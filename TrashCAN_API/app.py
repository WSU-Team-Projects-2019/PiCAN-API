import sqlite3
import json
import datetime
import logging
import requests
import uuid
from time import sleep
from threading import Thread
from flask_apscheduler import APScheduler
from flask import Flask, request, g
from flask_restful import Resource, Api
from gpiozero import Button, OutputDevice
from hx711 import HX711
import config
import bc_scanner
import sch

# Setup scale amp
hx711 = HX711(
    dout_pin=config.conf['SCALE_DATA_PIN'],
    pd_sck_pin=config.conf['SCALE_CLOCK_PIN'],
    channel=config.conf['SCALE_CHANNEL'],
    gain=config.conf['SCALE_GAIN']
)

#Create objects for physical objects
lid_switch = Button(config.conf['LID_SWITCH_PIN)'])
lid_open_button = OutputDevice(config.conf['LID_OPEN_PIN'], active_high=False, initial_value=False)
lid_close_button = OutputDevice(config.conf['LID_CLOSE_PIN'], active_high=False, initial_value=False)
light = OutputDevice(config.conf['LIGHT_PIN'], active_high=False, initial_value=False)
fan = OutputDevice(config.conf['FAN_PIN'], active_high=False, initial_value=False)
led = OutputDevice(config.conf['LED_PIN'], active_high=False, initial_value=False)

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
    my_api.add_resource(ApiRoot, '/api')
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
    app.config.from_object(sch.Config())
    scheduler.init_app(app)
    scheduler.start()

    app.run()

# Watchdog to monitor db config table for changes
def start_change_monitor():
    change_id = config.get_last_change_id()
    while True:
        new_conf_id = config.get_last_change_id()
        if new_conf_id > change_id:
            config.load_config()
            change_id = new_conf_id
            # Restart scheduler with new values
            scheduler.shutdown()
            scheduler.start()
        sleep(config['WATCHDOG_SLEEP_TIMER'])

# Pauses any jobs for lights and/or fan and starts up barcode scanner
def start_lid_monitor():
    state = False
    while True:
        #If lid is open, pause job processing, start the scanner and read
        while lid_switch.is_active():
            if not state:
                state = True
                requests.post(config.conf['HOME_SERVER_URL'] + '/lid?status=1', timeout=0.2)
                bc_scanner.start_scanner()
                scheduler.pause()
            upc = bc_scanner.read()
            #Uploads return from read if not empty
            if not upc:
                bc_scanner.upload(upc)
            #Maybe add pause here
        #If lid was just closed, resume processing jobs, stop scanner, and upload a scale reading
        if state:
            state = False
            requests.post(config.conf['HOME_SERVER_URL'] + '/lid?status=0', timeout=0.2)
            bc_scanner.stop_scanner()
            scheduler.resume()
            r = requests.get('http://127.0.0.1/api/scale')
            uuid.uuid1()
            requests.post('http://127.0.0.1/api/weight/'+uuid.uuid1()+'?weight='+r.text)
        #Maybe need pause here
        #sleep(config.conf['LID_SLEEP_TIMER'])


def toggle_led(action):
    if config.conf['CLEANING_LED'] == 'true':
        if action == 'off':
            led.off()
        elif action == 'on':
            led.on()
        else:
            led.toggle()

class Index (Resource):
    def get(self):
        content = "<h1>This is an index page</h1>"
        return content

class ApiRoot(Resource):
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

        if action == 'close':
            lid_close_button.on()
            logging.info('Lid closed')
        elif action == 'open':
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
            toggle_led('off')
        elif action == 'on':
            light.on()
            toggle_led('on')
        elif action == 'toggle':
            light.toggle()
            toggle_led()
        else:
            return 400
        requests.post(config.conf['HOME_SERVER_URL'] + '/light?status=' + light.value, timeout=0.2)
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
            toggle_led('off')
        elif action == 'on':
            fan.on()
            toggle_led('on')
        elif action == 'toggle':
            fan.toggle()
            toggle_led()
        else:
            return 400
        requests.post(config.conf['HOME_SERVER_URL'] + '/fan?status=' + fan.value, timeout=0.2)
        return 'Success'

class Scale (Resource):
    def get(self):
        hx711.reset() #Maybe not necessary
        results = hx711.get_raw_data(config.conf['NUM_MEASUREMENTS'])
        return sum(results)/len(results) - config.conf['TARE']

    def put(self):
        hx711.reset()  # Maybe not necessary
        config.set_config('TARE', hx711.get_raw_data(config.conf['NUM_MEASUREMENTS']))
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
        weight_raw = request.args.get('weight')
        weight = weight_raw * config.conf['CONVERSION_FACTOR']
        conn.cursor().execute("INSERT INTO Weight ([weight_id],[timestamp],[weight],[weight_raw]) VALUES(?, ?, ?,?)",
                              (weight_id,time,weight,weight_raw))
        conn.commit()
        return weight_id

    def delete(self, weight_id):
        conn = get_db()
        result = conn.cursor().execute("DELETE FROM[Weight] WHERE weight_id = ?",(weight_id,))
        conn.commit()
        return result

class ConfigList (Resource):
    def get(self):
        return config.get_config()

class ConfigItem (Resource):
    def get(self, option_name):
        return config.get_config(option_name)

    def put(self, option_name):
        value = request.args.get('value')
        config.set_config(option_name, value)

    def post(self, option_name):
        value = request.args.get('value')
        config.set_config(option_name, value)

    def delete(self, option_name):
        config.delete_config(option_name)



if __name__ == '__main__':
    t1 = Thread(target = start_api())
    t2 = Thread(target = start_change_monitor())
    t3 = Thread(target = start_lid_monitor())

    t1.start()
    t2.start()
    t3.start()

