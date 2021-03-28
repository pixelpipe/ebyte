"""
EBYTE E220-900T30D Library by pixelpipe
https://github.com/pixelpipe
"""

from machine import Pin, UART
from time import sleep
import binascii

MODE_NORMAL = 0
MODE_WAKEUP = 1
MODE_POWERDOWN = 2
MODE_PROGRAM = 3
RECOVER_DELAY = 0.04

class EbyteModule:
    def __init__(self, uart=1, rx = 5, tx = 4, m0=15, m1=14, aux=22):

        self.__br = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        self.__pr = ["8N1", "8O1", "8E1", "8N12"]
        self.__ar = ["2.4k", "2.4k", "2.4k", "4.8k", "9.6k", "19.2k", "38.4k", "62.5k"]
        self.__sp = ["200 bytes", "128 bytes", "64 bytes", "32 bytes"]
        self.__en = ["disabled", "enabled"]
        self.__tp = ["30dBm", "27dBm", "24dBm", "21dBm"]
        self.__tm = ["TTM", "FTM"]
        self.__wor = ["500ms", "1000ms", "1500ms", "2000ms", "2500ms", "3000ms", "3500ms", "4000ms"]

        self._moduleInfo = None
        self._moduleConfiguration = None
        self._writeResponse = None
        self._m0 = Pin(m0, Pin.OUT)  # Weak Pull UP , Pin.PULL_UP
        self._m1 = Pin(m1, Pin.OUT)  # Weak Pull UP , Pin.PULL_UP
        self._aux = Pin(aux, Pin.IN)
        self._tx = Pin(tx, Pin.OUT)
        self._rx = Pin(rx, Pin.IN)
        self._uart = UART(uart, 9600, bits=8, parity=None, stop=1, tx=self._tx, rx=self._rx)
        self.line = ""
        self.init()

    def init(self):
        self._m0.value(0)
        self._m1.value(0)
        sleep(1)
        self.drainUartBuffer()
        self.waitForAuxLow(1000)

    def setMode(self, mode):
        sleep(RECOVER_DELAY)
        if mode == MODE_NORMAL:
            print("Set NORMAL mode")
            self._m0.value(0)
            self._m1.value(0)
        elif mode == MODE_WAKEUP:
            print("Set WAKEUP mode")
            self._m0.value(1)
            self._m1.value(0)
        elif mode == MODE_POWERDOWN:
            print("Set POWER DOWN mode")
            self._m0.value(0)
            self._m1.value(1)
        elif mode == MODE_PROGRAM:
            print("Set PROGRAM mode")
            self._m0.value(1)
            self._m1.value(1)

        sleep(RECOVER_DELAY)

        self.drainUartBuffer()
        self.waitForAuxLow(1000)

    def configuration(self):
        return {
            'addr': 0x0000,
            'br': '9600',
            'pr': '8N1',
            'ar': '2.4k',
            'sp': '200 bytes',
            'rsn': 'disabled',
            'tp': '21dBm',
            'ch': 23,
            'rb': 'disabled',
            'tm': 'TTM',
            'lbt': 'disabled',
            'wor': '500ms',
            'ck': 0x0000
        }

    def drainUartBuffer(self):
        """Read until no chars in the serial buffer"""
        print("Draining UART buffer")

        if not self._uart.any():
            return

        while self._uart.any():
            read = self._uart.read(1)
            print(read, end="")

        print(" - Drained")

    def waitForAuxLow(self, timeout):
        """Wait until AUX goes low"""
        print("Waiting for AUX low")
        countdown = timeout / 100
        while self._aux.value == 1:
            print("Timeout Countdown: {}".format(countdown))
            countdown -= 1
            if countdown < 0:
                print("Timeout")
                return
            sleep(0.1)
        print("Module Ready")

    def readConfiguration(self):
        self.setMode(MODE_PROGRAM)
        self._uart.write(bytes([0xC1, 0x00, 0x08]))
        self._moduleInfo = bytearray(3 + 8)
        print("Reading module info")
        bytesRead = self._uart.readinto(self._moduleInfo)
        reg = 0
        self._moduleInfo = self._moduleInfo[3:]
        cfg = self._moduleInfo
        for b in cfg:
            print("REG {:02x}H = {:02x} [{:08b}]".format(reg, b, b))
            reg += 1
        print("# REG 0x01 and 0x02")
        print(" Address     : 0x{:04x}".format(256 * cfg[0] + cfg[1]))
        print(" Baudrate    : {}".format(self.__br[(cfg[2] & 0b11100000) >> 5]))
        print(" Parity      : {}".format(self.__pr[(cfg[2] & 0b00011000) >> 3]))
        print(" Air Datarate: {}".format(self.__ar[cfg[2] & 0b111]))
        print("# REG 0x03")
        print(" Sub Packet Setting : {}".format(self.__sp[(cfg[3] & 0b11000000) >> 6]))
        print(" RSSI Ambient Noise : {}".format(self.__en[(cfg[3] & 0b00100000) >> 5]))
        print(" Transmitting Power : {}".format(self.__tp[(cfg[3] & 0b00000011)]))
        print("# REG 0x04")
        print(" Channels : 850.125 + {} * 1M".format(cfg[4]))
        print("# REG 0x05")
        print(" Enable RSSI Byte    : {}".format(self.__en[(cfg[5] & 0b10000000) >> 7]))
        print(" Transmission Method : {}".format(self.__tm[(cfg[5] & 0b01000000) >> 6]))
        print(" LBT       : {}".format(self.__en[(cfg[5] & 0b00010000) >> 4]))
        print(" WOR Cycle : {}".format(self.__wor[(cfg[5] & 0b00000111)]))
        print("# REG 0x06 and 0x07")
        print(" Key : 0x{:04x}".format(256 * cfg[6] + cfg[7]))
        self.setMode(MODE_NORMAL)
        self.waitForAuxLow(1000)

    def writeConfiguration(self):
        cfg = self.configuration()
        self.setMode(MODE_PROGRAM)

        r0 = (cfg['addr'] & 0b1111111100000000) >> 8
        r1 = cfg['addr'] & 0b0000000011111111
        br = self.__br.index(cfg['br'])
        pr = self.__pr.index(cfg['pr'])
        ar = self.__ar.index(cfg['ar'])
        r2 = br << 5 | pr << 3 | ar
        sp = self.__sp.index(cfg['sp'])
        rsn = self.__en.index(cfg['rsn'])
        tp = self.__tp.index(cfg['tp'])
        r3 = sp << 6 | rsn << 4 | tp
        r4 = cfg['ch']
        rb = self.__en.index(cfg['rb'])
        tm = self.__tm.index(cfg['tm'])
        lbt = self.__en.index(cfg['lbt'])
        wor = self.__wor.index(cfg['wor'])
        r5 = rb << 7 | tm << 6 | lbt << 4 | wor
        r6 = (cfg['ck'] & 0b1111111100000000) >> 8
        r7 = cfg['ck'] & 0b0000000011111111
        self._uart.write(bytes([0xc0, 0x00, 0x08, r0, r1, r2, r3, r4, r5, r6, r7]))
        self._writeResponse = bytearray(8)
        bytesRead = self._uart.readinto(self._writeResponse)
        #print(binascii.hexlify(self._writeResponse))
        self.setMode(MODE_NORMAL)
        self.waitForAuxLow(1000)

    def readLine(self):
        if self._uart.any():
            return self._uart.readline()
        else:
            return None

    def sendLine(self, line):
        print("Sending [{}]".format(line))
        self._uart.write(line + "\n")

    def printAux(self):
        print(self._aux.value())
