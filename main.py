import rp2
import network
import ubinascii
import machine
import time

from wificonfig import wificonfig
import socket

# Set country to avoid possible errors
rp2.country('SG')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode
# wlan.config(pm = 0xa11140)

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('mac = ' + mac)

# Load login data from different file for safety reasons
ssid = wificonfig['ssid']
pw = wificonfig['pw']

wlan.connect(ssid, pw)

#setup LEDs and potentiometer
led = machine.Pin('LED', machine.Pin.OUT)
redLed = machine.Pin(15, machine.Pin.OUT)
pot = machine.ADC(26);

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)
    redLed.toggle()

# Define blinking function for onboard LED to indicate error codes
def blink_onboard_led(num_blinks):
    led = machine.Pin('LED', machine.Pin.OUT)
    for i in range(num_blinks):
        led.on()
        time.sleep(.2)
        led.off()
        time.sleep(.2)
    led.on()

# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth

wlan_status = wlan.status()
blink_onboard_led(wlan_status)

if wlan_status != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    print('Connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    led.on()

# Function to load in html page
def get_html(html_name):
    with open(html_name, 'r') as file:
        html = file.read()

    return html


# HTTP server with socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print('Listening on', addr)

# Listen for connections
while True:
    
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706)/0.001721
    
    cl, addr = s.accept()
    
    try:        
        print('Client connected from', addr)
        rcv = cl.recv(2048)
        # print(rcv)
        r = str(rcv)
        print(r)
        led_on = r.find('redled=on')
        led_off = r.find('redled=off')
        led_blink = r.find('led=blink')
        print('led_on = ', led_on)
        print('led_off = ', led_off)
        if led_on > -1:
            print('LED ON')
            redLed.value(1)

        if led_off > -1:
            print('LED OFF')
            redLed.value(0)
        
        if led_blink > -1:
            print('LED Blink')
            blink_onboard_led(10)
            
        potV = 100 * (pot.read_u16() / 3000);

        response = '{ '
        response = response + '"redled": "' + str(redLed.value()) + '", '
        response = response + '"pot": "' + str(potV) + '", '
        response = response + '"temp": "' + str(temperature) + '" '
        response = response + ' }'
        
        cl.send('HTTP/1.0 200 OK\r\nContent-type:application/vnd.api+json\r\nAccess-Control-Allow-Origin:*\r\n\r\n')
        cl.send(response)
        cl.close()
        
    except OSError as e:
        cl.close()
        print('Connection closed')

# Make GET request
# request = requests.get('http://www.google.com')
# print(request.content)
# request.close()
