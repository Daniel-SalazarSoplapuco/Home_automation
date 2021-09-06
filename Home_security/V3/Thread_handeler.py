from Radar import Radar
from queue import Queue
import threading
import time as tm

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
        

class thread_handeler():

    def __init__(self, name, process_object, run_object_name):
        self.name = name
        self.process_object = process_object
        self.run_object_name = run_object_name
        self.thread_object = object
        self.stop_event = threading.Event()

    def start(self):
        self.process_object.stop_event = self.stop_event
        self.thread_object = threading.Thread(target=getattr(self.process_object, self.run_object_name ))
        # self.thread_object = threading.Thread(target=self.process_object.run)
        self.thread_object.daemon = True
        self.thread_object.start()

    def stop(self):
        self.stop_event.set()
        self.thread_object.join()

    def restart(self):
        self.stop()
        self.stop_event.clear()
        self.start()
    
    def is_alive(self):
        return self.thread_object.is_alive()

class multiple_thread_handeler():

    def __init__(self):
        self.running_threads = {}

    def initalize_thread(self, name, process_object, run_object_name):
        # init should contain a variable stop_event which should be used to indicate when a process should stop
        self.running_threads[name] = thread_handeler(name, process_object, run_object_name)
        self.running_threads[name].start()

    def stop_specific_thread(self, name):
        self.running_threads[name].stop()

    def stop_all_threads(self):
        for key in self.running_threads:
            self.running_threads[key].stop()

    def restart_specific_thread(self, name):
        self.running_threads[name].restart()

    def restart_all_threads(self):
        for key in self.running_threads:
            self.running_threads[key].restart()

    def is_specific_thread_alive(self, name):
        return self.running_threads[name].is_alive()

    def return_living_threads(self):
        living_list = []
        for key in self.running_threads:
            living_list.append([key, self.running_threads[key].is_alive()])
        return living_list


if __name__ == '__main__':

    process1 = test_thread_class(name=1)
    process2 = test_thread_class(name=2)
    process3 = test_thread_class(name=3)

    multiple_threads = multiple_thread_handeler()
    multiple_threads.initalize_thread('test1', process1, 'run')
    multiple_threads.initalize_thread('test2', process2, 'run')
    multiple_threads.initalize_thread('test3', process3, 'run')
    tm.sleep(3)
    print(multiple_threads.return_living_threads())
    
    print('Stop all threads')
    multiple_threads.stop_all_threads()
    
    print('All threads should be false {}'.format( multiple_threads.return_living_threads()))
    tm.sleep(2)
    
    print('Restarting all threads')
    multiple_threads.restart_all_threads()
    tm.sleep(1)
    print(multiple_threads.return_living_threads())
    tm.sleep(3)

