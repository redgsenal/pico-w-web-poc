from machine import Pin
from utime import sleep

btn = Pin(12, Pin.IN, Pin.PULL_UP)  # button switch
pin = Pin(11, Pin.OUT)              # yellow LED

print("LED starts flashing...")
while True:
    pin.value((btn.value()))