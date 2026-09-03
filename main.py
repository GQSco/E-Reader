"""
Raspberry Pi Pico W + Waveshare 2.13" e-Paper (V3) - Landscape Mode

Wiring assumed:
    
    EReader:
        RST_PIN  = 16
        DC_PIN   = 20
        CS_PIN   = 21
        BUSY_PIN = 17
        SCK_PIN  = 18   (SPI0 hardware SCK)
        DIN_PIN  = 19   (SPI0 hardware MOSI/TX)
    
    SDCard reader:
        CS   = 13
        SCK  = 10
        MOSI = 11
        MISO = 12
    
    Button Inputs:
        Up     = 2
        Down   = 3
        Select = 4
        
"""

import time
from library import Book
from E_Reader import EReader
from sdcard_transfer import mount_SDCard

if __name__ == '__main__':
    # Define Objects
    sd_objects = mount_SDCard()
    
    app = EReader()
    
    app.run()



