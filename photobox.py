# -*- coding: utf-8 -*
import logging
import time
import uuid
import Adafruit_BluefruitLE
from datetime import datetime
import subprocess
import requests
import json
import os
from threading import Thread
from PIL import Image
import RPi.GPIO
import Adafruit_ILI9341 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

# reset du BT
command = "sudo hciconfig hci0 reset"
os.system(command)


UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

ble = Adafruit_BluefruitLE.get_provider()

LED = 18

RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(LED, RPi.GPIO.OUT)
pwm = RPi.GPIO.PWM(LED, 1000)
brightness = 50 # Brightness value must be between 0 (min) and 100 (max)
pwm.start(brightness)


DC = 23
RST = 25
SPI_PORT = 0
SPI_DEVICE = 0
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

disp.begin()
disp.clear((255, 0, 0))
disp.display()





def mainBle():

    camera_offline = 1
    previous_camera_offline = 1

    # Clear any cached data because both bluez and CoreBluetooth have issues with
    # caching data and it going stale.
    ble.clear_cached_data()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print('Disconnecting any connected UART devices...')
    ble.disconnect_devices([UART_SERVICE_UUID])

    # Scan for UART devices.
    print('Searching for UART device...')
    try:
        adapter.start_scan()
        # Search for the first UART device found (will time out after 60 seconds
        # but you can specify an optional timeout_sec parameter to change it).
        device = ble.find_device(service_uuids=[UART_SERVICE_UUID])
        if device is None:
            raise RuntimeError('Failed to find UART device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()

    print('Connecting to device...')
    device.connect()

    try:
        print('Discovering services...')
        device.discover([UART_SERVICE_UUID], [TX_CHAR_UUID, RX_CHAR_UUID])
        uart = device.find_service(UART_SERVICE_UUID)
        rx = uart.find_characteristic(RX_CHAR_UUID)
        tx = uart.find_characteristic(TX_CHAR_UUID)

        def received(data):
            timer()
            date_today = datetime.now()
            nom_image = date_today.strftime('%d_%m_%H_%M_%S')

            #on prend la photo
            chemin_photo = '/home/pi/Desktop/photos/'+nom_image+'.jpg'
            takepic(chemin_photo) #on prend la photo 

            image = Image.open("wait.jpg")
            disp.display(image)            

        # Turn on notification of RX characteristics using the callback above.
        print('Subscribing to RX characteristic changes...')
        rx.start_notify(received)

        while True:
          time.sleep(1)
          camera_offline = subprocess.call(["ping", "192.168.122.1", "-c1", "-W2", "-q"], stdout=open(os.devnull, 'w'))
          if camera_offline == 1:
            print("camera offline")
            image = Image.open("offline.jpg")
            disp.display(image)

          else:
            # si la camera viens tout juste d'être allumée il faut l'initialiser
            if previous_camera_offline == 1:
              print("camera wakeup")
              data = {"method":"startRecMode", "params":[], "id":1, "version":"1.0"}
              response = requests.post('http://192.168.122.1:8080/sony/camera', json=data)

              image = Image.open("wait.jpg")
              disp.display(image)   

          previous_camera_offline = camera_offline

    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()
        mainBle()


def takepic(imageName):
    print("mode photo")
    data = {"method":"setShootMode", "params":["still"], "id":1, "version":"1.0"}
    response = requests.post('http://192.168.122.1:8080/sony/camera', json=data)
    print(response.status_code)

    data = {"method":"actTakePicture", "params":[], "id":1, "version":"1.0"}
    response = requests.post('http://192.168.122.1:8080/sony/camera', json=data)
    print(response.text)
    json_data = json.loads(response.text)


    image = Image.open("processing.jpg")
    disp.display(image)

    url = json_data["result"][0][0]
    url = url.replace("Scn", "Origin")
    r = requests.get(url, stream=True)

    with open(imageName, 'wb') as fd:
        for chunk in r.iter_content(2000):
            fd.write(chunk)

    #Google sync
    command = "rclone sync -v /home/pi/Desktop/photos gdmedia:/gopro"
    os.system(command)

    image = Image.open("done.jpg")
    disp.display(image)
    time.sleep(3)


def timer():
  #image = Image.open('5.jpg')
  #disp.display(image)
  #time.sleep(1)
  #image = Image.open('4.jpg')
  #disp.display(image)
  #time.sleep(1)
  image = Image.open('3.jpg')
  disp.display(image)
  time.sleep(1)
  image = Image.open('2.jpg')
  disp.display(image)
  time.sleep(1)
  image = Image.open('1.jpg')
  disp.display(image)
  time.sleep(1)

  image = Image.open('0.jpg')
  disp.display(image)

ble.initialize()
ble.run_mainloop_with(mainBle)