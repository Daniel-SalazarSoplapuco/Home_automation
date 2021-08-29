from queue import Queue
import threading
import datetime as dt
import time as tm
import RPi.GPIO as GPIO
from gpiozero import MotionSensor
from Telegram_bot import Telegram_bot
from Telegram_bot_extended import TelegramBot
from File_manager import FileManager
from Camera import Camera
import passwords as pw
import os

MAX_QSIZE = 100  # max queue size

class Radar:
    def __init__(self, queue):
        self.queue = queue

    def run(self):
        Radar = MotionSensor(20)
        
        Thread = "Radar"
        Message = "[Radar]: Motion detected at [{}]".format(dt.datetime.now())
        Arguments = [True, dt.datetime.now()]
        
        while True:
            Radar.wait_for_inactive()
            Thread = "Radar"
            Message = "[Radar]: Motion detected at [{}]".format(dt.datetime.now())
            Arguments = [True, dt.datetime.now().strftime("%Y%m%d %H:%M:%S")]
            self.queue.put([Thread, Message, Arguments])
            tm.sleep(1)

class Consumer:
    def __init__(self, queue):
        self.queue = queue
        self.Telegram_bot = TelegramBot("Home", pw.telegram_pw(), pw.one_time_password(), self.queue)
        # self.Telegram_bot = Telegram_bot(pw.telegram_pw())
        self.Camera = Camera()
        
        self.armed = False
        self.return_feed = False
        
    def run(self):
        while True:
            item = self.queue.get()
            return_argument = "no handeler for this command"
            if item[0] == "Telegram":
                return_argument = self.telegram_handeler(item)
            elif item[0] == "Radar":
                return_argument = self.radar_handeler(item)
            feed_message = "Consumer: " + return_argument[1] + " " + item[1]
            print(feed_message)
            if self.return_feed:
                self.Telegram_bot.send_message(self.Telegram_bot.return_admin(), feed_message)
            self.queue.task_done()
    
                
def main():
    
    q = Queue(maxsize=MAX_QSIZE)

    radar_producer = Radar(q)
    radar_thread = threading.Thread(target=radar_producer.run)

    consumer = Consumer(q)
    consumer_thread = threading.Thread(target=consumer.run)

    radar_thread.start()
    consumer_thread.start()

if __name__ == "__main__":
    main()
    