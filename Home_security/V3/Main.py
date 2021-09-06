from Radar import Radar
from queue import Queue
from Camera import Camera
import threading
import time as tm
from Thread_handeler import multiple_thread_handeler

class RaspberryHome():


    def __init__(self):
        self.queue = Queue(maxsize=100)
        self.process_handelers = {}
        self.Camera = Camera()
        
        self.telegram_bot = None
        self.telegram_commands = None

        self.home_security_armed = False

        self.queue_dictionary_process = {'radar': self.handle_home_security}

    def start_home_security(self, simulation=False):
        #start the radar detection process and post to the queeu in seperate thread
        # -> add start restart process for home security if home security not in dict of mutliple_thread_handelere then start, if not invoke mutliple_thread_handelere restart of all related threads
        self.process_handelers['home_security'] = multiple_thread_handeler()
        process = Radar(delay=2, queue_object=self.queue)
        self.process_handelers['home_security'].initalize_thread('radar', process, 'run_simulated')

    def handle_home_security(self, arguments):
        # invoke actions if radar detects any movement and if user has armed security
        if self.home_security_armed:


        else:
            pass

    def telegram_start_restart(self):
        # if telegram wasn't started yet start, if started already restart with new variables
        if self.telegram_bot = None:
            self.telegram_bot = TelegramBot("Home", config.telegram_pw(), config.one_time_password(), self.queue, psuedo_commands=self.telegram_commands)
            self.telegram_bot.run()
        else:
            self.telegram_bot.terminate()
            self.telegram_bot = TelegramBot("Home", config.telegram_pw(), config.one_time_password(), self.queue, psuedo_commands=self.telegram_commands)
            self.telegram_bot.run()

    def telegram_add_command(self, command):
        # add commands to telegram if telegram was already started restart telegram with new commands
        # -> still needs to be added: if restart of telegram is required save all user object temporarily and pass these back to telegram on restart
        if type(command) == list:
            self.telegram_commands.extend(command)
        else:
            self.telegram_commands.append(command)

        if self.telegram_bot != None:
            self.start_restart_telegram()

    def run(self):
        # start listing to queue from different threads
        while True:
            item = self.queue.get()
            print(item)

            #handle variable requests
            self.queue_dictionary_process[item[0]](item[0][2])

            self.queue.task_done()
            tm.sleep(1)
            print(self.process_handelers['home_security'].return_living_threads())




if __name__ == '__main__':
    process = RaspberryHome()
    # process.start_home_security()
    # process.run()
    process.take_picture()

    

