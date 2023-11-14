import sys
import smbus
import time
import atexit
import threading
from dbm import DBMeter
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput

###############################################
# Camera setup.
picam2 = Picamera2()
fps = 30
dur = 5
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig['controls']['FrameDurationLimits'] = (micro, micro)
encoder = H264Encoder()
picam2.configure(vconfig)

a = DBMeter("sound_meter_thread")
a.set_queue_duration(10)
##############

output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.h264"
picam2.start_recording(encoder, output)

def cleanup():
    picam2.stop_()
    a.join()
    print(a.queue)

if (__name__ == "__main__"):
    atexit.register(picam2.stop_)
    a.start()