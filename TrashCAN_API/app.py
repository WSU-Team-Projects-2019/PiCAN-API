import sqlite3
import json
import uuid
import datetime
import logging
from flask import Flask, request, g
from flask_restful import Resource, Api, reqparse
from gpiozero import Button, OutputDevice
from hx711 import HX711
import config

app = Flask(__name__)
api = Api(app)

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
DATABASE = '/srv/trashcan/venv/database.db'

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
    def post(self,barcode):
        conn = get_db()
        barcode_id = uuid.uuid1()
        time = datetime.datetime.now()
        conn.cursor().execute("INSERT INTO ([barcode_id],[timestamp],[barcode]) VALUES(?, ?, ?)",(barcode_id,time,barcode,))
        conn.commit()
        return barcode_id

    def delete(self, barcode_id):
        conn = get_db()
        result = conn.cursor().execute("DELETE FROM[Barcode] WHERE barcode_id = ?",(barcode_id,))
        conn.commit()
        return result


class Weight (Resource):
    def post(self):
        conn = get_db()
        weight_id = uuid.uuid1()
        time = datetime.datetime.now()
        weight = request.args.get('weight')
        conn.cursor().execute("INSERT INTO ([weight_id],[timestamp],[weight]) VALUES(?, ?, ?)",(weight_id,time,weight,))
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

class Config (Resource):
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


#Map resource
api.add_resource(Index, '/')
api.add_resource(Api, '/api')
api.add_resource(Lid, '/api/lid')
api.add_resource(Scale, '/api/scale')
api.add_resource(Light, '/api/light')
api.add_resource(Fan, '/api/fan')
api.add_resource(BarcodeList, '/api/barcode')
api.add_resource(WeightList, '/api/weight')
api.add_resource(Barcode, '/api/barcode/<barcode_id>')
api.add_resource(Weight, '/api/weight/<weight_id>')
api.add_resource(ConfigList, 'api/config')
api.add_resource(Config, 'api/config/<option_name>')

if __name__ == '__main__':
    app.run()
