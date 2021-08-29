import datetime as dt
import time as tm
import RPi.GPIO as GPIO
from gpiozero import MotionSensor
  
           
Radar = MotionSensor(20)


while True:
    Radar.wait_for_inactive()
    print("detected {}".format(dt.datetime.now()))
    tm.sleep(2)