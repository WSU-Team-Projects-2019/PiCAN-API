# Not much here now, but will need to add more as we figure out how to use the barcode scanner

def read():
    f = open('/dev/ttyACM0')
    return f.read(13)