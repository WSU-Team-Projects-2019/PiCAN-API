# import logging
import config
import requests
import uuid
from gpiozero import OutputDevice
import select

bc_trigger = OutputDevice(config.conf['BC_TRIGGER_PIN'], active_high=False, initial_value=False)


def read():
    hid = {4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k', 15: 'l',
           16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x',
           28: 'y', 29: 'z', 30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7', 37: '8', 38: '9', 39: '0',
           44: ' ', 45: '-', 46: '=', 47: '[', 48: ']', 49: '\\', 51: ';', 52: '\'', 53: '~', 54: ',', 55: '.', 56: '/'}

    hid2 = {4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K', 15: 'L',
            16: 'M', 17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X',
            28: 'Y', 29: 'Z', 30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&', 37: '*', 38: '(', 39: ')',
            44: ' ', 45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':', 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'}

    fp = open(config.conf['BARCODE_SCANNER_PATH'], 'rb')

    bc = ""
    shift = False
    done = False

    #Wait for 1 second on any input from /dev file. Returns barcode or empty string
    r, w, e = select.select([fp], [], [], 1)
    if fp in r:
        while not done:
            buffer = fp.read(8)
            for c in buffer:
                if c > 0:
                    #40 is CR, means done
                    if int(c) == 40:
                        done = True
                        break;
                    if shift:
                        #2 is shift key
                        if int(c) == 2:
                            shift = True
                        #Use shift charset
                        else:
                            bc += hid2[int(c)]
                            shift = False
                    else:
                        if int(c) == 2:
                            shift = True
                        #Use non-shifted charset
                        else:
                            bc += hid[int(c)]
        return bc
    else:
        return ''

def start_scanner():
    bc_trigger.on()

def stop_scanner():
    bc_trigger.off()

# Attempt to upload barcode directly to server, otherwise store locally
def upload(bc):
    try:
        requests.post(config.conf['HOME_SERVER_URL']+'/barcode-lookup?upc='+bc, timeout=0.2)
    except requests.exceptions as e:
        requests.post('http://127.0.0.1/api/barcode/'+uuid.uuid1()+'?barcode='+bc)