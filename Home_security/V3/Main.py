from Radar import Radar
from queue import Queue
import threading
import time as tm
from Thread_handeler import multiple_thread_handeler

class test_thread_class():
    
    def __init__ (self, name,  stop_event = object, delay = 1):
        self.stop_event = stop_event
        self.name = name

    def run(self):
        for x in range(0, 10):
            print("{} is still running {} of 10" .format(self.name, x))
            tm.sleep(1)

            if self.stop_event.is_set():
                break


class RaspberryHome():


    def __init__(self):
        self.queue = Queue(maxsize=100)
        self.process_handelers = {}

    def start_home_security(self):
        self.process_handelers['home_security'] = multiple_thread_handeler()
        process = Radar(delay=2, queue_object=self.queue)
        self.process_handelers['home_security'].initalize_thread('radar', process)

    def test_run(self):
        while True:
            item = self.queue.get()
            print(item)
            self.queue.task_done()
            tm.sleep(1)
            print(self.process_handelers['home_security'].return_living_threads())

if __name__ == '__main__':
    process = RaspberryHome()
    process.start_home_security()
    process.run()

    

