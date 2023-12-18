from collections import deque
import sys
import smbus
import time
import threading
from queue import Queue
from datetime import datetime,timedelta
from sleep_until import sleep_until
###############################################
# Constants

# I2C address
PCBARTISTS_DBM = 0x48

# Registers
I2C_REG_VERSION		= 0x00
I2C_REG_ID3			= 0x01
I2C_REG_ID2			= 0x02
I2C_REG_ID1			= 0x03
I2C_REG_ID0			= 0x04
I2C_REG_SCRATCH		= 0x05
I2C_REG_CONTROL		= 0x06
I2C_REG_TAVG_HIGH	= 0x07
I2C_REG_TAVG_LOW	= 0x08
I2C_REG_RESET		= 0x09
I2C_REG_DECIBEL		= 0x0A
I2C_REG_MIN			= 0x0B
I2C_REG_MAX			= 0x0C
I2C_REG_THR_MIN     = 0x0D
I2C_REG_THR_MAX     = 0x0E
I2C_REG_HISTORY_0	= 0x14
I2C_REG_HISTORY_99	= 0x77

i2c = smbus.SMBus(1)

def reg_write(i2c, addr, reg, data):
    """
    Write bytes to the specified register.
    """
    
    # Write out message to register
    i2c.write_byte_data(addr, reg, data)
    
def reg_read(i2c, addr, reg, nbytes=1):
    """
    Read byte(s) from specified register. If nbytes > 1, read from consecutive
    registers.
    """
    
    # Check to make sure caller is asking for 1 or more bytes
    if nbytes < 1:
        return bytearray()
    
    # Request data from specified register(s) over I2C
    data = i2c.read_i2c_block_data(addr, reg, nbytes)
    
    return data
###############################################
# Functions

class DBMeter(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.fifo = deque
        i2c = smbus.SMBus(1)
        self.db_level = 0
        self.prev_ts = datetime.now()
        self.wake_time = datetime.now() + timedelta(0,500)
        # Read device ID to make sure that we can communicate with the ADXL343
        data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_VERSION)
        print("dbMeter VERSION = 0x{:02x}".format(int.from_bytes(data, "big")))

        data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_ID3, 4)
        print("Unique ID: 0x{:02x} ".format(int.from_bytes(data, "big")))

        #Set values to 
        reg_write(i2c,PCBARTISTS_DBM,I2C_REG_TAVG_HIGH,0x00)
        reg_write(i2c,PCBARTISTS_DBM,I2C_REG_TAVG_LOW,0x7D)
        self.queue_length = 80 # 10 s* 8 sps
    
    def set_queue_duration(self,duration_in_secs):
        self.queue_length = 8*duration_in_secs
        self.fifo = deque(maxlen=self.queue_length)

    def set_callback(self,callback):
        self.cb = callback


    def capture(self):
        ts = datetime.now()
        data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_DECIBEL)
        self.db_level = int.from_bytes(data, "big")
        self.fifo.append(tuple([ts,self.db_level]))
        #print("Sound Level (dB SPL) = {:3d}".format(self.db_level))
        #print("{:3d}".format(self.db_level), end=" ")
        #print(ts-self.prev_ts)
        self.prev_ts = ts
        self.wake_time = ts + timedelta(0,0.125)
    
    def run(self):
        self.trigger=False
        self.trailing_cycle_count = 3*self.queue_length/4
        while True:
            if self.trigger:
                if self.trailing_cycle_count < 0:
                    break
                else:
         #           print(self.trailing_cycle_count)
                    self.trailing_cycle_count = self.trailing_cycle_count - 1
            self.capture()
            if not self.trigger and self.db_level > 65:
                self.trigger = True
            sleep_until(self.wake_time.timestamp())




