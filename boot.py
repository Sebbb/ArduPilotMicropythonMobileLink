# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import time
import machine
import select
import network
import socket
import sys

from config import config


def read_all(uart):
 while not uart.any():
   x=1 # do nothing :|
 data = True
 while data:
  data = uart.read()
  if data:
   sys.stdout.write(data)

def gsm_setup():
    global ppp
    modem_uart.read() # ignore all prev. data

    modem_uart.write('AT+CSTT="%s","%s","%s"\r\n' % (config.modem_apn, config.modem_user, config.modem_password))
    read_all(modem_uart)

    modem_uart.write("AT+CREG?\r\n")
    read_all(modem_uart)

    modem_uart.write("AT+CPIN?\r\n")
    read_all(modem_uart)

    modem_uart.write("AT+CREG?\r\n")
    read_all(modem_uart)

    modem_uart.write("AT+CNMI=0,0,0,0,0\r\n")
    read_all(modem_uart)

    modem_uart.write('AT+CGDCONT=1,"IP","%s"\r\n' % config.modem_apn)
    read_all(modem_uart)

    modem_uart.write('AT+CGDATA="PPP",1\r\n')
    time.sleep(0.1)
    print(modem_uart.readline())
    print(modem_uart.readline())
    ppp = network.PPP(modem_uart)

    ppp.active(True)
    ppp.connect()
    return(ppp)

def wifi_setup():
    global wifi
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(config.client_wifi_ssid, config.client_wifi_password)

def wifi_ap_setup():
    global ap
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=config.ap_wifi_ssid, password=config.ap_wifi_password, authmode=network.AUTH_WPA_WPA2_PSK)
    ap.active(True)

def test_connect():
  addr_info = socket.getaddrinfo("towel.blinkenlights.nl", 23)
  addr = addr_info[0][-1]
  s = socket.socket()
  s.connect(addr)
  while True:
    data = s.recv(500)
    print(str(data, 'utf8'), end='')

def wait_for_modem_ready():
    global modem_uart
    global modem_ena_pin
    import utime
    print("waiting for modem")
    while True:
        buf=b''
        start=utime.ticks_us()
        while utime.ticks_us()-start < 30*1000000: # 30 seconds
            ret = select.select([modem_uart], [], [], 1) # 1 seconds
            if modem_uart.any():
                buf+=modem_uart.read()
            if b"\r\nCall Ready\r\n" in buf:
                return True
            buf=buf[-100:]
            x=sys.stdout.write('.')
        print(" didn't get a ready from modem, resetting")
        modem_ena_pin.off()
        time.sleep(1)
        modem_ena_pin.on()

def passthrough():
    if False: # for new modems
        print("forward setup..\n")
        modem_uart = machine.UART(1, tx=27, rx=26)
        modem_uart.init(115200, bits=8, parity=None, stop=1)
        time.sleep(1)
        modem_uart.write("AT+IPR=460800;&W\r")  # stores this...
        time.sleep(0.1)
        print(modem_uart.read())
        modem_uart.init(460800, bits=8, parity=None, stop=1)
    
    print("forwarding..\n")
    modem_uart.write("ATE1\r") # enables echo
    exec(open('./forward.py').read(),globals())



gnd_pin=machine.Pin(32, machine.Pin.OUT)
gnd_pin.off()

switch1_pin=machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP)
switch2_pin=machine.Pin(33, machine.Pin.IN, machine.Pin.PULL_UP)

ppp=None
ap=None

listen=None
destination= None

if switch1_pin.value()==1 and switch2_pin.value()==1:
    sys.exit(0)

if switch1_pin.value()==0:  # AP mode
    print("wifi mode")
    #wifi_ap_setup()
    wifi_setup()
    # wait for IP
    while not wifi.isconnected():
        time.sleep(0.2)
        x=sys.stdout.write('.')
    listen=wifi.ifconfig()[0] # my IP
    print("IP", listen)
    
if switch2_pin.value()==0:  # Modem mode
    print("modem mode")
    
    destination = (config.forward_dest, config.forward_port)
    
    # enable and configure Modem already
    modem_ena_pin = machine.Pin(23, machine.Pin.OUT)
    modem_ena_pin.on()

    modem_uart = machine.UART(1, tx=27, rx=26)
    modem_uart.init(460800, bits=8, parity=None, stop=1)

    # def get_ip():
        # modem._write("AT+CIFSR\r")
        # count=0
        # while count<30:
            # count+=1
            # ip = modem.uart.read()
            # time.sleep(0.5)
            # if ip:
                # return ip.strip()

    #if mpin.value() == 0:
    #    passthrough()

    wait_for_modem_ready()

    time.sleep(1)

    ppp=gsm_setup()

    time.sleep(1)

    while not ppp.isconnected():
      time.sleep(0.2)
      x=sys.stdout.write('.')


import fc_forward
fc_forward.forward(listen, destination)

