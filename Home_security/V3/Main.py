from Radar import Radar
from queue import Queue
from Camera import Camera
from Telegram_bot import TelegramBot
import config
import threading
import time as tm
from Thread_handeler import multiple_thread_handeler

def string_to_int(string):
    try:
        string_int = int(string)
        return string_int
    except ValueError:
        # Handle the exception
        return False


class RaspberryHome():

    def __init__(self):
        self.queue = Queue(maxsize=100)
        self.process_handelers = {}
        self.return_feed = False

        self.Camera = Camera()

        self.telegram_dictionary_functions = {'arm_security': self.home_security_arm, 'disarm_security': self.home_security_disarm,
                                                'start_security': self.start_restart_home_security, 'stop_security': self.stop_home_security, 
                                                'restart_telegram': self.start_restart_telegram, 'stop_telegram': self.stop_telegram,
                                                'start_return_feed': self.start_return_feed, 'stop_return_feed': self.stop_return_feed,
                                                'send_picture': self.home_security_send_picture, 'set_delay': self.home_security_set_delay,
                                                'stop_program': self.stop_program}
        self.telegram_bot = None

        self.home_security_armed = False
        self.home_security_delay = 2

        self.queue_dictionary_functions = {
            'Radar': self.handle_home_security, 'Telegram': self.handle_telegram}

    def start_restart_home_security(self, simulation=False):
        # start the radar detection process and post to the queeu in seperate thread
        if 'home_security' in self.process_handelers:
            self.process_handelers['home_security'].restart_all_threads()
        else:
            self.process_handelers['home_security'] = multiple_thread_handeler()
            process = Radar(delay=self.home_security_delay, queue_object=self.queue)
            self.process_handelers['home_security'].initalize_thread(
                'Radar', process, 'run')

    def stop_home_security(self, context=None):
        if 'home_security' in self.process_handelers:
            self.process_handelers['home_security'].stop_all_threads()
            del self.process_handelers['home_security']

    def handle_home_security(self, arguments):
        # invoke actions if radar detects any movement and if user has armed security
        print("Radar message gramted [{}] arguments: {}".format(self.home_security_armed, arguments))
        if self.home_security_armed:
            self.telegram_bot.send_message(self.telegram_bot.return_admin(), "[Home security] Motion has been detected below a picture of the motion")
            self.home_security_take_pictures(self.telegram_bot.return_admin(), 1)
        else:
            pass

    def home_security_take_pictures(self, to_whom, amount_of_pictures):
        for a in range(amount_of_pictures):
            self.telegram_bot.send_image(to_whom, self.Camera.picture())

    def home_security_send_picture(self, context=None):
        self.home_security_take_pictures(self.telegram_bot.return_admin(), 1)

    def home_security_set_delay(self, context=None):
        user_id = self.telegram_bot.return_admin()
        if context is not None and context:
            if string_to_int(context[0]):
                self.home_security_delay = string_to_int(context[0])
                self.stop_home_security()
                self.start_restart_home_security()
                self.telegram_bot.send_message(user_id, "[Home security] Succesfull of setting delay [{}] and restarting home security".format(self.home_security_delay))
            else:
                self.telegram_bot.send_message(user_id, "[Home security] Variable provided [{}] is not an intiger and cannot be accepted as delay".format(context[0]))
        else:
            self.telegram_bot.send_message(user_id, "[Home security] Set variable by using command '/set_delay X', X being the variable")

    def home_security_arm(self, context=None):
        self.home_security_armed=True

    def home_security_disarm(self, context=None):
        self.home_security_armed=False

    def start_restart_telegram(self, context=None):
        # if telegram wasn't started yet start, if started already restart with new variables
        if self.telegram_bot is None:
            self.start_telegram()
        else:
            self.telegram_bot.terminate()
            self.start_telegram()

    def start_telegram(self, context=None):
        self.telegram_bot=TelegramBot("Home", config.telegram_pw(), config.one_time_password(), 
        self.queue, psuedo_commands=list(self.telegram_dictionary_functions.keys()))
        self.telegram_bot.create_admin()
        self.telegram_bot.run()

    def stop_telegram(self, context=None):
        if self.telegram_bot is not None:
            self.telegram_bot.terminate()
            self.telegram_bot=None

    def telegram_add_command(self, command):
        # add commands to telegram if telegram was already started restart telegram with new commands
        # -> still needs to be added: if restart of telegram is required save all user object temporarily and pass these back to telegram on restart
        if type(command) == list:
            self.telegram_commands.extend(command)
        else:
            self.telegram_commands.append(command)

        if self.telegram_bot != None:
            self.start_restart_telegram()

    def handle_telegram(self, arguments):
        print("Telegram message arguments: {}".format(arguments))
        arguments = arguments[2]
        if arguments[0]:
            telegram_command = arguments[3][1:]
            if telegram_command in self.telegram_dictionary_functions:
                self.telegram_dictionary_functions[telegram_command](arguments[4])
            else:
                pass


    def start_return_feed(self, context=None):
        self.return_feed = True

    def stop_return_feed(self, context=None):
        self.return_feed = False

    def handle_return_feed(self, arguments):
        if self.return_feed and self.telegram_bot is not None:
            feed_message = 'Queue granted [{}] message: {}'.format(arguments[2][0], arguments[1])
            self.telegram_bot.send_message(self.telegram_bot.return_admin(), feed_message)

    def run(self):
        # start listing to queue from different threads
        while True:
            # get latest task from the queue task
            item=self.queue.get()

            # return queue tasks to user through telegram 
            self.handle_return_feed(item)

            # handle variable requests
            self.queue_dictionary_functions[item[0]](item)

            self.queue.task_done()
            
            # tm.sleep(1)
            # print(
            #     self.process_handelers['home_security'].return_living_threads())

    def stop_program(self, context=None):
        self.stop_home_security()
        self.stop_telegram()
        self.stop_return_feed()
        exit()


if __name__ == '__main__':
    process=RaspberryHome()
    # process.start_restart_home_security()
    # process.run()
    process.return_feed = True
    process.start_restart_telegram()
    process.start_restart_home_security()
    process.run()
