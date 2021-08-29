from queue import Queue
import threading
import datetime as dt
import time as tm
import RPi.GPIO as GPIO
from gpiozero import MotionSensor
from Telegram_bot import TelegramBot
from File_manager import FileManager
from Camera import Camera
import passwords as pw
import os
import sys

class Radar:
    def __init__(self, queue):
        self.queue = queue
        self.stop = False

    def run(self):
        Radar = MotionSensor(20)
        
        Thread = "Radar"
        Message = "[Radar]: Motion detected at [{}]".format(dt.datetime.now())
        Arguments = [True, dt.datetime.now()]
        
        while not self.stop:
            Radar.wait_for_inactive()
            Thread = "Radar"
            Message = "[Radar]: Motion detected at [{}]".format(dt.datetime.now())
            Arguments = [True, dt.datetime.now().strftime("%Y%m%d %H:%M:%S")]
            self.queue.put([Thread, Message, Arguments])
            tm.sleep(1)

    def terminate(self):
        self.stop = True      

class RaspberryHome(object):
    
    def __init__(self):
        self.queue = Queue(maxsize=100)
        
        self.armed = False
        self.return_feed = False
        
        self.telegram_commands = {'/arm_security': self.arm, '/disarm_security': self.disarm, '/picture': self.take_picture, '/video': self.record_video,
                         '/status': self.status, '/start_return_feed': self.start_return_feed, '/stop_return_feed': self.stop_return_feed, 
                         '/shutdown': self.shutdown}
        
        self.Camera = Camera()
        self.Telegram_bot = TelegramBot("Home", pw.telegram_pw(), pw.one_time_password(), self.queue, psuedo_commands=self.telegram_commands.keys())
        self.Radar_producer = Radar(self.queue)
        self.Radar_thread = threading.Thread(target=self.Radar_producer.run)
        self.Radar_thread.daemon = True
        self.Radar_thread.start()
    
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
        
    def radar_status(self):
        return self.Radar_thread.is_alive()
        
    def disarm(self):
        self.armed = False
        
    def arm(self):
        self.armed = True
    
    def take_picture(self):
        self.Telegram_bot.send_image(self.Telegram_bot.return_admin(), self.Camera.picture())
    
    def record_video(self):
        # self.Telegram_bot.send_video(self.Telegram_bot.return_admin(), self.Camera.video())
        self.Telegram_bot.send_file(self.Telegram_bot.return_admin(), self.Camera.file())
    
    def status(self):
        message = 'Raspberry_home: is online, the status of thread radar is [{}], the status armed is [{}] \n the status of return feed is [{}]'.format(
            self.radar_status(), self.armed, self.return_feed)
        self.Telegram_bot.send_message(self.Telegram_bot.return_admin(), message)
    
    def start_return_feed(self):
        self.return_feed = True
        
    def stop_return_feed(self):
        self.return_feed = False
    
    def shutdown(self):
        self.Telegram_bot.send_message(self.Telegram_bot.return_admin(), 'Shutting down Raspberry_home')
        self.Telegram_bot.terminate()
        sys.exit()
        
    def do_nothing(self):
        pass
        
    def telegram_handeler_set(self, commands, functions):
        self.telegram_commmand_dict = dict(zip(commands, functions))
        
    def telegram_handeler(self, arguments):
        arguments =  arguments[2]
        if arguments[1] and arguments[4]:
            if arguments[2] in self.telegram_commands:
                self.telegram_commands[arguments[2]]()
                return [True, "Granted"]
            elif arguments[2] in self.Telegram_bot.command_dict.keys():
                return [True, "Granted"]
            else:
                return [False, "Unknown command"]
        else:
            return [False, "Not admin"]
                
    def radar_handeler(self, arguments):
        arguments =  arguments[2]
        if self.armed and arguments[0]:
            self.take_picture()
            return [True, "Picture taken"]
        else:
            return [False, "Not armed"]
        
if __name__ == "__main__":
    Raspberry = RaspberryHome()
    Raspberry.run()
    test()