# -*- coding: utf-8 -*
import RPi.GPIO
import time
from datetime import datetime
from PIL import Image
import os
import Adafruit_ILI9341 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

from goprocam import GoProCamera
from goprocam import constants
import urllib.request




#non attribué
LED = 18



RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(LED, RPi.GPIO.OUT)
pwm = RPi.GPIO.PWM(LED, 1000)
brightness = 50 # Brightness value must be between 0 (min) and 100 (max)
pwm.start(brightness)



GPIO_BUTTON = 26
DC = 23
RST = 25
SPI_PORT = 0
SPI_DEVICE = 0
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

disp.begin()
disp.clear((255, 0, 0))
disp.display()


RPi.GPIO.setmode(RPi.GPIO.BCM)
RPi.GPIO.setup(GPIO_BUTTON, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)

gpCam = GoProCamera.GoPro()


def takepic(imageName): #prend une photo (note: il faut selectionner la ligne qui correspond Ã  votre installation en enlevant le premier # )
    print("on prend une photo: " + imageName)

    #prise d'une photo avec la GoPro
    photoUrl = gpCam.take_photo(0)

    #on affiche un message de traitement
    image = Image.open('processing.jpg')
    disp.display(image)

    #téléchargement de la photo depuis la GoPro
    urllib.request.urlretrieve(photoUrl, imageName)

    #suppression de l'effet fisheye
    command = "convert "+imageName+" -distort barrel '0.06335 -0.18432 -0.13009' "+imageName+"_fix"
    os.system(command)


    #Google sync
    command = "rclone sync -v /home/pi/Desktop/photos gdmedia:/gopro"
    os.system(command)

def loadpic(imageName): # affiche imagename
    image = Image.open("done.jpg")
    #image = image.resize((240, 320)).rotate(90+180)

    disp.display(image)
    time.sleep(5)
    print("loading image: " + imageName)


def minuterie():
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


def writemessage(message): # pour pouvoir afficher des messages sur un font noir 
    print("affiche message: " + message)


def writemessagetransparent(message): # pour pouvoir afficher des messages en conservant le font 
    print("affiche message: " + message)


if (os.path.isdir("/home/pi/Desktop/photos") == False): # si le dossier pour stocker les photos n'existe pas       
   os.mkdir("/home/pi/Desktop/photos")                  # alors on crÃ©e le dossier (sur le bureau)
   os.chmod("/home/pi/Desktop/photos",0o777)            # et on change les droits pour pouvoir effacer des photos


while True : #boucle jusqu'a interruption
  try:
        print("attente boucle")

        image = Image.open('wait.jpg')
        disp.display(image)        

        #on attend que le bouton soit pressÃ©
        RPi.GPIO.wait_for_edge(GPIO_BUTTON, RPi.GPIO.FALLING)
        # on a appuyÃ© sur le bouton...


        #on lance le decompte
        minuterie()


        #on genere le nom de la photo avec heure_min_sec
        date_today = datetime.now()
        nom_image = date_today.strftime('%d_%m_%H_%M_%S')

       
        #on prend la photo
        chemin_photo = '/home/pi/Desktop/photos/'+nom_image+'.jpg'
        takepic(chemin_photo) #on prend la photo 

        #on affiche la photo
        loadpic(chemin_photo)

        #on affiche un message
        writemessagetransparent("et voila...")

        if (RPi.GPIO.input(GPIO_BUTTON) == 0): #si le bouton est encore enfoncÃ© (sont etat sera 0)
              print("bouton  appuye, je dois sortir")
              break # alors on sort du while 
             

  except KeyboardInterrupt:
    print("sortie du programme!")
    raise

RPi.GPIO.cleanup()           # reinitialisation GPIO lors d'une sortie normale
disp.clear()
