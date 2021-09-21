import time as tm
from picamera import PiCamera
import datetime as dt
import os
from File_manager import FileManager
import datetime as dt
import subprocess
from subprocess import call
from queue import Queue
import threading

class CameraThread(object):

    def __init__(self, stop_event: object = object, queue_object :object = None):
        
        self.thread_name = 'PiCamera'
        self.queue_object = queue_object.put
        self.stop_event = stop_event
    
        self.FM = FileManager("Camera_thread")
        self.FM.folder_handler_multiple([['Picture', 'output'],['Record','output'],['Record','converted']],['picture_output','record_output', 'record_converted'])


        self.camera = PiCamera()
        self.camera.resolution = (800, 600)
        self.camera.rotation  = 180
        self.camera.framerate = 24
        self.camera.annotate_text = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.camera.annotate_text_size = 18

        # capture pictures while recording during thread
        self.video_picture_capture = True

        # How long should the video last
        self.loop_time = 5

        # how many pictures should be taken during the loop
        self.loop_pictures = 5
        self.loop_delay = self.loop_time/self.loop_pictures  

        # delay for picture loop
        self.picture_delay = 1

    def ffmpeg_h264_to_mp4(self, from_path):
        # convert video output from raspberry pi as out put is in h264 format
        to_path = os.path.join(self.FM.get_folder('record_converted'), os.path.basename(os.path.splitext(from_path)[0])) +".mp4"
        command = "ffmpeg -hide_banner -loglevel quiet -framerate 24 -i {} -c copy {}".format(from_path, to_path)
        # command = "ffmpeg -i {} -c copy {}".format(from_path, to_path)
        os.system(command)
        # call([command], shell=True)
        return to_path

    def queue_picture(self, output_path):
        #post path of picture to queue
        print('picture passed back to queue')
        self.queue_object([self.thread_name, '[PiCamera] picture captured', ['picture', output_path, dt.datetime.now().strftime("%Y%m%d %H:%M:%S %f")]])
        
    def queue_video(self, output_path):
        #post path of video to queue
        print('video passed back to queue')
        self.queue_object([self.thread_name, '[PiCamera] video captured', ['video', output_path, dt.datetime.now().strftime("%Y%m%d %H:%M:%S %f")]])

    def picture_path(self):
        # create path where to place a picture
        name = 'picture_{}.jpg'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('picture_output')
        file_path_name = os.path.join(path, name)
        return file_path_name
    
    def video_path(self):
        # create path where to place a video
        name = 'video_{}.h264'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('record_output')
        file_path_name = os.path.join(path, name)
        return file_path_name

    def record_picture_loop(self):
        self.lock_camera()
        # record and take pictures for x amount of time and post this to the queue
        previous_video_path = None

        with self.camera as camera:
            while True:
                video_path = self.video_path()
                camera.start_recording(video_path)

                if previous_video_path:
                    self.queue_video(self.ffmpeg_h264_to_mp4(previous_video_path))

                for a in range(self.loop_time):
                    if self.video_picture_capture:
                        picture_path = self.picture_path()
                        camera.capture(picture_path, use_video_port=True)
                        self.queue_picture(picture_path)
                    camera.wait_recording(self.loop_delay)

                camera.stop_recording()
                previous_video_path = video_path

                if self.stop_event.is_set():
                    if previous_video_path:
                        self.queue_video(self.ffmpeg_h264_to_mp4(previous_video_path))
                    else:
                        self.queue_video(self.ffmpeg_h264_to_mp4(video_path))
                    self.release_camera()
                    break
                else:
                    self.request_stop_event()
    
    def request_stop_event(self):
        self.queue_object([self.thread_name, '[PiCamera] Camera recording requests stop event', ['request_stop_event', True, dt.datetime.now().strftime("%Y%m%d %H:%M:%S %f")]])

    def picture_loop(self):
        with self.camera as camera:
            while True:
                picture_path = self.picture_path()
                camera.capture(picture_path)
                self.queue_picture(picture_path)
                tm.sleep(self.picture_delay)
                if self.stop_event.is_set():
                    break

    def picture(self):
        name = 'image_{}.jpg'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('picture_output')
        file_path_name = os.path.join(path, name)
        self.camera.capture(file_path_name)
        self.ffmpeg_h264_to_mp4(file_path_name)
        return file_path_name

    def picture_thread(self):
        self.lock_camera()
        self.queue_picture(self.picture())
        self.release_camera()

    def video_h264(self, duration=5):
        name = 'video_{}.h264'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('record_output')
        file_path_name = os.path.join(path, name)
        
        self.camera.resolution = (800, 600)
        self.camera.start_recording(file_path_name)
        self.camera.wait_recording(duration)
        self.camera.stop_recording()

        return file_path_name        

    def video_mp4(self, duration=5):
        return self.ffmpeg_h264_to_mp4(self.video_h264(duration))

    def video_mp4_thread(self, duration=5):
        self.lock_camera()
        self.queue_video(self.video_mp4())
        self.release_camera()

    def release_camera(self):
        self.queue_object([self.thread_name, '[PiCamera] Camera_object released', ['released', True, dt.datetime.now().strftime("%Y%m%d %H:%M:%S %f")]])

    def lock_camera(self):
        self.queue_object([self.thread_name, '[PiCamera] Camera_object locked', ['released', False, dt.datetime.now().strftime("%Y%m%d %H:%M:%S %f")]])

class CameraClass(object):

    def __init__(self, rotation=180):
        # depreciated
        self.camera = PiCamera()
        self.camera.rotation = rotation
        self.camera.resolution = (800, 600)
        self.camera.framerate = 24
        self.camera.annotate_text = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.camera.annotate_text_size = 18
        self.split_rec_seconds = 5
        self.FM = FileManager("Camera")
        self.FM.folder_handler_multiple([['Picture', 'output'],['Record','output'],['Record','converted']],['picture_output','record_output', 'record_converted'])
        tm.sleep(1)

    def ffmpeg_h264_to_mp4(self, from_path):
        to_path = os.path.join(self.FM.get_folder('record_converted'), os.path.basename(os.path.splitext(from_path)[0])) +".mp4"
        command = "ffmpeg -hide_banner -loglevel quiet -preset ultrafast -framerate 24 -i {} -c copy {}".format(from_path, to_path)
        os.system(command)
        # call([command], shell=True)
        return to_path

    def mp4box_h264_to_mp4(self, from_path):
        to_path = os.path.join(self.FM.get_folder('record_converted'), os.path.basename(os.path.splitext(from_path)[0])) +".mp4"
        command = "MP4Box -fps 24 -add {} {}".format(from_path, to_path)
        call([command], shell=True)
        return to_path

    def picture(self):
        name = 'image_{}.jpg'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('picture_output')
        file_path_name = os.path.join(path, name)
        self.camera.capture(file_path_name)
        return file_path_name

    def video_h264(self, duration):
        name = 'video_{}.h264'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('record_output')
        file_path_name = os.path.join(path, name)
        
        self.camera.resolution = (800, 600)
        self.camera.start_recording(file_path_name)
        self.camera.wait_recording(duration)
        self.camera.stop_recording()

        return self.ffmpeg_h264_to_mp4(file_path_name)        


    def video_mp4(self, duration):
        return self.ffmpeg_h264_to_mp4(self.video_h264(duration))


if __name__ == '__main__':
    # run = Camera()
    # run.ffmpeg_h264_to_mp4(run.video())
    # run.FM.deep_clean_folder('picture_output')
    # run.FM.deep_clean_folder('record_output')
    
    queue_object = Queue(maxsize=100)
    stop_event= threading.Event()
    process = CameraThread(stop_event=stop_event, queue_object=queue_object)

    camera_thread_thread = threading.Thread(target=process.picture_thread)
    camera_thread_thread.daemon = True
    camera_thread_thread.start()
    
    while True:
        if not queue_object.empty():
            item = queue_object.get()
            print(item)
            queue_object.task_done()
        else:
            print("Object is empty, is thread alive {}".format(camera_thread_thread.is_alive()))
        tm.sleep(1)

