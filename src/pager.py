"""
Basic LoRa Pager by pixelpipe
https://github.com/pixelpipe
"""

import utime
from utime import sleep
from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
import framebuf
from ebyte import EbyteModule


class Pager:
    def __init__(self):
        self._e220 = EbyteModule(uart=1, rx = 5, tx = 4, m0=15, m1=14, aux=22)
        self._led = Pin(25, Pin.OUT)
        self._button = Pin(6, Pin.IN, Pin.PULL_DOWN)
        self._oldButtonValue = -1
        self._currentButtonValue = 0
        self._counter = 0
        self._timeMarker = utime.ticks_ms()
        self.autosend = False
        self.initScreen()
        self.configureLoRa()

    def configureLoRa(self):
        self._e220.writeConfiguration()
        self._e220.readConfiguration()

    def initScreen(self):
        try:
            self._i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
            self._oled = SSD1306_I2C(128, 64, self._i2c)
            self._logo = framebuf.FrameBuffer(
                bytearray(
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
                32, 32,
                framebuf.MONO_HLSB)
            self._oled.fill(0)
            self._oled.blit(self._logo, 96, 64 - 32)
            self._oled.text("PIXELPAGER PICO", 0, 0)
            self._oled.show()
            self._hasDisplay = True
            print("Display initialised")
        except:
            self._hasDisplay = False

    def buttonPressed(self):
        self._led.value(1)
        self._e220.sendLine(self.getMessage())
        print("Button Pressed")

    def buttonDepressed(self):
        print("Button Depressed")
        self._led.value(0)

    def getMessage(self):
        self._counter += 1
        return "Quick fox jumps over the lazy dog for {} times.".format(self._counter)

    def scanButtons(self):
        self._currentButtonValue = self._button.value()
        if self._currentButtonValue != self._oldButtonValue:
            if self._currentButtonValue == 1 and self._oldButtonValue == 0:
                self.buttonPressed()
            else:
                self.buttonDepressed()
        self._oldButtonValue = self._currentButtonValue

    def printMessage(self, message):
        x = 0
        y = 0
        x0 = 0
        y0 = 0
        index = 0
        for c in message:
            self._oled.text(chr(c), x0 + x, y0 + y)
            x += 8
            if x > 127:
                x = 0
                y += 8
            if y > 127:
                break

        self._oled.show()

    def loop(self):

        # READ LORA
        line = self._e220.readLine()
        if line != None:
            self._led.value(1)
            print(line)
            self._oled.fill(0)
            self.printMessage(line)
            self._led.value(0)

        # SCAN BUTTONS
        self.scanButtons()

        # AUTOSEND
        if self.autosend:
            if utime.ticks_diff(utime.ticks_ms(), self._timeMarker) > 1000 * 2:
                self._led.value(1)
                self._e220.sendLine(self.getMessage())
                self._led.value(0)                
                self._timeMarker = utime.ticks_ms()

    @staticmethod
    def heartbeat(gp=25):
        pwm = PWM(Pin(gp))
        pwm.freq(1000)
        for duty in range(25025):
            pwm.duty_u16(duty)
            sleep(0.0001)
        for duty in range(25025, 0, -1):
            pwm.duty_u16(duty)
            sleep(0.0001)


