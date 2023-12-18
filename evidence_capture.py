import sys
import smbus
import time
import atexit
from dbm import DBMeter
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Encoder
from picamera2.outputs import CircularOutput
from typing import Deque
from threading import Thread
from buffered_output import BufferedOutput
from matplotlib import pyplot as plt
from smb.SMBConnection import SMBConnection
from PIL import Image
import numpy as np
#import cv2
from matplotlib import animation
from datetime import datetime
import os
import gc
from collections import deque
import tracemalloc

###############################################
# Camera setup.
picam2 = Picamera2()
fps = 24
dur = 10
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig['controls']['FrameDurationLimits'] = (micro, micro)
#vconfig['main']['size']=(1920,1080)
encoder = Encoder()
picam2.configure(vconfig)
interval = 0.125
##############
output = BufferedOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)


def cleanup():
    picam2.stop_recording()
    picam2.stop_()
    picam2.close()

# def startLoop():
#     threading.Timer(interval,startLoop).start()
#     a.capture()

def reportTimeBrackets(ts,arr):
    print("time now:", end=" ")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("video start: ", end=" ")
    print(ts[0].strftime("%Y-%m-%d %H:%M:%S"))
    print("video end: ", end=" ")
    print(ts[-1].strftime("%Y-%m-%d %H:%M:%S"))
    print("data start: ", end=" ")
    print(arr[0,0].strftime("%Y-%m-%d %H:%M:%S"))
    print("data end: ", end=" ")
    print(arr[-1,0].strftime("%Y-%m-%d %H:%M:%S"))
    return
    
    

def produceBaseFigure(trigger_time_string,plot_lims,sz):
    fig, (ax1, ax2) = plt.subplots(2,1,figsize=(10,8),gridspec_kw={'height_ratios':[3,1],'hspace':0.05,'wspace':0.05})
    ax1.axis('off')
    img = ax1.imshow(np.zeros((sz[1],sz[0],4),np.uint8))
    fig.set_dpi(100)
    fig.suptitle("Capture Triggered at: " + trigger_time_string + " UTC Time\n" +
                 "Red line on plot is 76 dBA limit per MCL 257.707c(1)(c)(ii).\n" + 
                 "Orange lines are per residential noise limits, Sec. 46-181 for Day (55 dBA) and Night (50 dBA) per table.\n" +
                 "Sensor has accuracy +/- 2dB. Set to 'A' weighted network and sampled over 125ms(ANSI S1.4-1971).")
    ax2.grid(b=True, which='major', color='k', linestyle='-')
    ax2.axhline(y=76,color='r')
    ax2.axhline(y=55,color='tab:orange')
    ax2.axhline(y=50,color='tab:orange')
    ax2.set_ylabel('Sound Level [dBA]')
    db_line, = ax2.plot([],[], color="b")
    ax2.set_xlim(plot_lims[0], plot_lims[1])
    ax2.set_ylim(plot_lims[2], plot_lims[3])
    return fig, img, db_line
    
def animate(i,img, db_line,arr,video_frames,timestamp_deque,sz):
    img.set_array(np.reshape(np.frombuffer(video_frames[i], dtype=np.uint8),(sz[1],sz[0],4)))
    #find latest timestamp
    x_data =[]
    y_data =[]
    ts = timestamp_deque[i]
    k = 0; 
    while k < len(arr[:,0]) and arr[k,0] < ts : 
        x_data.append(arr[k,0])
        y_data.append(arr[k,1])
        k=k+1
    db_line.set_data(x_data,y_data)
    return [db_line, img]

def generateVideoViaFunc(data_buffer,video_frames,timestamp_deque,vconfig):
    video_frames_l = video_frames.copy()
    print("video_frames_l size:")
    print(sys.getsizeof(video_frames_l))
    ts_deque = timestamp_deque.copy()
    arr = np.asarray(data_buffer)
    reportTimeBrackets(ts_deque,arr)
    sz = vconfig['main']['size']
    # pull the data in as a np array
    db_max = arr.max(axis=0)[1]
    db_min = arr.min(axis=0)[1]
    plot_lims = [ts_deque[0],ts_deque[-1],db_min-2, max(db_max+2,80)]
    trigger_data_frame = 0
    for i in range(len(data_buffer)):
        if data_buffer[i][1] > 65:
            trigger_data_frame = i
            print(i, end=" ")
            print("is trigger frame")
            break
    
    # set the title
    fig, img, db_line = produceBaseFigure(arr[trigger_data_frame,0].strftime("%Y-%m-%d %H:%M:%S"),plot_lims,sz)      
    #time.sleep(0.05)              
    ani = animation.FuncAnimation(fig, animate, frames=len(video_frames_l), fargs=(img, db_line,arr,video_frames_l,ts_deque,sz), interval=41.6,repeat=False, blit=True)
    writergif = animation.PillowWriter(fps=24)
    date_name = arr[trigger_data_frame,0].strftime("%Y_%m_%d_%H_%M_%S") + ".gif"
    output_file = "/dev/shm/" + date_name
    try: 
        ani.save(output_file,writer=writergif)
        print(date_name, end=" ")
        print("file saved to ram")
    except Exception as e:
        print("FAILURE ON SAVE")
        print(e)
        print(type(e))

    file_obj = open(output_file,'rb')
    conn = SMBConnection("soundmeter","ihearyou","soundmeter", "boxotubes", use_ntlm_v2 = True)
    connection_result = conn.connect('192.168.1.10')
    if connection_result:
        print("[SMB connection] success")
    else:
        print("[SMB connection] failure")
    
    try:
        print("attempting_upload")
        ret = conn.storeFile('SoundMeter', date_name, file_obj)
    except:
        print("upload fail")
        conn.close()
        file_obj.close()
        os.remove(output_file)
    else:
        if ret > 0:
            print("upload success")
        else:
            print("upload fail")

    conn.close()
    file_obj.close()
    os.remove(output_file)
    return date_name

import linecache
def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))
    return


if (__name__ == "__main__"):
    atexit.register(cleanup)
    tracemalloc.start(10)
    threads = deque()
    while True:
        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot)
        print("restarting loop")
        if threads:
            while not threads[0].is_alive():
                print("deleting finished threads")
                t = threads.popleft()
                t.join()
        output.reset()
        gc.collect()
        picam2.start_recording(encoder, output)
        #print(picam2.capture_metadata()["SensorTimestamp"])
        a = DBMeter("sound_meter_thread")
        a.set_queue_duration(10)
        a.start()
        a.join()
        #print("stop camera enter: " + datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
        #print("reference time was: ", end=" ")
        #print(output.reference_time.strftime("%Y-%m-%d %H:%M:%S"))
        picam2.stop_recording()
        output.stop()
        #print("stop camera exit: " + datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
        #print('exiting thread')
        threads.append(Thread(target=generateVideoViaFunc,args=(a.fifo.copy(),output.getFrames(),output.getTimestamps(),vconfig,)))
        threads[-1].start()
        #generateVideoViaFunc(hold_fifo,output.getFrames(),output.getTimestamps(),vconfig)
    cleanup()


        
