import sys
import smbus
import time
import atexit
import threading
from dbm import DBMeter
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput
import concurrent.futures

###############################################
# Camera setup.
picam2 = Picamera2()
fps = 24
dur = 10
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig['controls']['FrameDurationLimits'] = (micro, micro)
encoder = H264Encoder(10000000)
picam2.configure(vconfig)
interval = 0.125
##############

output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.h264"

def cleanup():
    picam2.stop_()

def startLoop():
    threading.Timer(interval,startLoop).start()
    a.capture()


def processVideo(data_buffer,video_file_path):
    print("fired video process function")
    for time,db in data_buffer:
        print(time.strftime("%m/%d/%Y, %H:%M:%S.%fUTC")," ",str(db),"dB")
    print("ending video process function")

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
if (__name__ == "__main__"):
    atexit.register(cleanup)
    hold_fifo = 0
    while True:
        picam2.start_recording(encoder, 'test.file',pts='timestamp.txt')
        a = DBMeter("sound_meter_thread")
        a.set_queue_duration(10)
        a.start()
        a.join()
        hold_fifo = a.fifo
        print('exiting thread')
        # output.stop()
        picam2.stop_recording()
        picam2.stop_()
        executor.submit(processVideo,hold_fifo,'test.file')


