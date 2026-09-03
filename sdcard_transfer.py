import machine
import sdcard
import os

sdcard_clk = 10
sdcard_MOSI = 11
sdcard_MISO = 12
sdcard_cs = 13

def mount_SDCard():
    if not "sd" in os.listdir("/"):
        # Set up SPI
        spi = machine.SPI(1, baudrate=1000000, polarity=0, phase=0, sck=machine.Pin(sdcard_clk), mosi=machine.Pin(sdcard_MOSI), miso=machine.Pin(sdcard_MISO))
        cs = machine.Pin(sdcard_cs)
        
        # Initialize the SD card
        sd = sdcard.SDCard(spi, cs)

        # Mount the SD card file system
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
    
    return spi, sd, vfs

if __name__ == "__main__":
    mount_SDCard()
    print(os.listdir("/sd"))


