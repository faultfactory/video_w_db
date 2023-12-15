import sys
import smbus
import time
import atexit
import threading
from dbm import DBMeter
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Encoder
from picamera2.outputs import CircularOutput
import concurrent.futures
from buffered_output import BufferedOutput

###############################################
# Camera setup.
picam2 = Picamera2()
fps = 24
dur = 10
size=(1280,780)
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig['controls']['FrameDurationLimits'] = (micro, micro)
encoder = Encoder()
picam2.configure(vconfig)
interval = 0.125
##############
video_file_increment = 0;

def cleanup():
    picam2.stop_()

def startLoop():
    threading.Timer(interval,startLoop).start()
    a.capture()


def processVideo(data_buffer,video_frames,timestamp_deque):
    print("fired video process function")
    for time,db in data_buffer:
        print(time.strftime("%m/%d/%Y, %H:%M:%S.%fUTC")," ",str(db),"dB")
    print("ending video process function")

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
if (__name__ == "__main__"):
    atexit.register(cleanup)
    hold_fifo = 0
    while True:
        file_name = str(video_file_increment).zfill(6)
        video_file_name = file_name+'.h264'
        output = BufferedOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
        picam2.start_recording(encoder, output)
        print(picam2.capture_metadata())
        a = DBMeter("sound_meter_thread")
        a.set_queue_duration(10)
        a.start()
        a.join()
        hold_fifo = a.fifo
        print('OUTPUT STOP FUNCTION')
        output.stop()
        executor.submit(processVideo,hold_fifo,output.getFrames(),output.getTimestamps())
        picam2.stop_recording()
        picam2.stop_()
        video_file_increment = video_file_increment + 1


