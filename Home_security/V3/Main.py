from Radar import Radar
from queue import Queue
import threading
import time as tm

class RaspberryHome():


    def __init__(self):
        # self.queue = Queue(maxsize=100)
        self.queue = None
        self.stop_threads = {}

    def kill_threads(self):
        for key in self.stop_threads:
            self.stop_threads[key].set()

    def kill_specific_thread(self, key):
        self.stop_threads[key].set()

    def restart_threads(self):
        pass


    def initialize_radar_thread(self):
        self.stop_threads['radar'] = threading.Event()
        process = Radar(queue_object=self.queue, delay=1, stop_event=self.stop_threads['radar'])
        
        radar_thread = threading.Thread(target=process.run)
        radar_thread.daemon = True
        radar_thread.start()


if __name__ == '__main__':
    run = RaspberryHome()
    run.initialize_radar_thread()
    tm.sleep(5)
    print('kill radar')
    run.kill_specific_thread('radar')

    

