from Radar import Radar
from queue import Queue
from Camera_handeler import CameraThread
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

        self.start_restart_camera()

        self.telegram_dictionary_functions = {'arm_security': self.home_security_arm, 'disarm_security': self.home_security_disarm,
                                                'start_security': self.start_restart_home_security, 'stop_security': self.stop_home_security, 
                                                'restart_telegram': self.start_restart_telegram, 'stop_telegram': self.stop_telegram,
                                                'start_return_feed': self.start_return_feed, 'stop_return_feed': self.stop_return_feed,
                                                'send_picture': self.camera_thread_picture, 'send_video': self.camera_thread_video,
                                                 'stop_program': self.stop_program,  'trigger_home_security': self.handle_home_security}
        self.telegram_bot = None

        self.home_security_armed = False
        self.home_security_video_picture = True
        self.home_secutity_motion_detection_time = tm.time()
        self.home_security_motion_detection_delay = 7
        self.camera_released = True

        self.home_security_delay = 1

        self.queue_dictionary_functions = {
            'Radar': self.handle_home_security, 'Telegram': self.handle_telegram, 'PiCamera': self.handle_camera_response}

    def start_restart_home_security(self, simulation=False):
        # start the radar detection process and post to the queeu in seperate thread
        if simulation:
            run = 'run_simulated'
        else:
            run = 'run'

        if 'home_security' in self.process_handelers:
            self.process_handelers['home_security'].restart_all_threads()
        else:
            self.process_handelers['home_security'] = multiple_thread_handeler()
            process = Radar(delay=self.home_security_delay, queue_object=self.queue)
            self.process_handelers['home_security'].initalize_thread(
                'Radar', process, run)

    def run_home_security_simulated(self, context=None):
        self.start_restart_home_security(simulation=True)


    def stop_home_security(self, context=None):
        if 'home_security' in self.process_handelers:
            self.process_handelers['home_security'].stop_all_threads()
            del self.process_handelers['home_security']

    def handle_home_security(self, arguments=None):
        # invoke actions if radar detects any movement and if user has armed security
        print("Radar message granted [{}] arguments: {}".format(self.home_security_armed, arguments))
        
        if self.home_security_armed and self.camera_released:
            self.camara_thread_start_recording()
            self.home_secutity_motion_detection_time = tm.time()
            self.telegram_bot.send_message(self.telegram_bot.return_admin(), "[Home security] Motion bas been detected started recording video and taking pictures")
        else:
            pass

    def handle_camera_response(self, arguments):
        granted = True
        if arguments[2][0] == 'picture':
            self.telegram_bot.send_image(self.telegram_bot.return_admin(),arguments[2][1])
        elif arguments[2][0] == 'video':
            self.telegram_bot.send_video(self.telegram_bot.return_admin(), arguments[2][1])
        elif arguments[2][0] == 'released':
            self.camera_released == arguments[2][1]
        elif arguments[2][0] == 'request_stop_event':
            if tm.time() - self.home_secutity_motion_detection_time > self.home_security_motion_detection_delay:
                self.camara_thread_stop_recording()
            else:
                granted = False

        print("Camera response command [{}], granted [{}]".format(arguments[2][0], granted))

    def camera_thread_picture(self, context=None):
        self.process_handelers['PiCamera'].initalize_thread('PiCamera', self.Camera, 'picture_thread')

    def camera_thread_video(self, context=None, duration=5):
        self.process_handelers['PiCamera'].initalize_thread('PiCamera', self.Camera, 'video_mp4_thread')

    def camara_thread_start_recording(self):
        self.process_handelers['PiCamera'].initalize_thread('PiCamera', self.Camera, 'record_picture_loop')

    def camara_thread_stop_recording(self):
        if 'PiCamera' in self.process_handelers:
            self.process_handelers['PiCamera'].stop_all_threads()

    def return_locked_camera_message(self):
        self.telegram_bot.send_message(self.telegram_bot.return_admin(), "[PiCamera] camera is locked cannot perform action")

    def start_restart_camera(self):
        if 'PiCamera' in self.process_handelers:
            self.process_handelers['PiCamera'].stop_all_threads()
        self.Camera = CameraThread(queue_object=self.queue)
        self.process_handelers['PiCamera'] = multiple_thread_handeler()

    def stop_camera(self):
        if 'PiCamera' in self.process_handelers:
            self.process_handelers['PiCamera'].stop_all_threads()
        self.Camera = CameraThread(queue_object=self.queue)

    def home_security_send_picture(self, context=None):
        if self.camera_released:
            self.camera_thread_picture()
        else:
            self.return_locked_camera_message()

    def home_security_send_video(self, context=5):
        if self.camera_released:
            if not str(context).isnumeric():
                context = 5
            else:
                context = int(str(context))
            self.camera_thread_video(context)
        else:
            self.return_locked_camera_message()

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
        self.start_telegram()
        self.telegram_bot.send_message(self.telegram_bot.return_admin(), 'We are live again')
        # start listing to queue from different threads
        while True:
            # get latest task from the queue task
            item=self.queue.get()
            print(item)
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
    process.return_feed = True
    # process.start_restart_telegram()
    # process.home_security_send_picture()
    # process.home_security_send_video(5)
    process.run()
