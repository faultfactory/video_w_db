import sys
import smbus
import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput

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

###############################################
# Functions

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
# Main

# Read device ID to make sure that we can communicate with the ADXL343
data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_VERSION)
print("dbMeter VERSION = 0x{:02x}".format(int.from_bytes(data, "big")))

data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_ID3, 4)
print("Unique ID: 0x{:02x} ".format(int.from_bytes(data, "big")))

#Set values to 
reg_write(i2c,PCBARTISTS_DBM,I2C_REG_TAVG_HIGH,0x00)
reg_write(i2c,PCBARTISTS_DBM,I2C_REG_TAVG_LOW,0x7D)



while True:
    picamera2.c
    data = reg_read(i2c, PCBARTISTS_DBM, I2C_REG_DECIBEL)
    print("Sound Level (dB SPL) = {:3d}".format(int.from_bytes(data, "big")))
    time.sleep(0.125)
sys.exit()



##############

output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.h264"
picam2.start_recording(encoder, output)
time.sleep(dur)
output.stop()