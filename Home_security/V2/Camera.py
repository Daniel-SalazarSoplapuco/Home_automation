import time as tm
from picamera import PiCamera
import datetime as dt
import os
from File_manager import FileManager
import datetime as dt
import subprocess
from subprocess import call 

def convert(file_h264):
    print(os.path.splitext("/path/to/some/file.txt")[0])
    command = "ffmpeg -i " + file_h264 + " " + file_mp4
    call([command], shell=True)

class Camera(object):

    def __init__(self, rotation=180):
        self.camera =camera = PiCamera()
        self.camera.rotation = rotation
        self.camera.resolution = (1280, 720)
        self.camera.framerate = 30
        self.camera.annotate_text = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.camera.annotate_text_size = 18
        self.split_rec_seconds = 5
        self.FM = FileManager("Camera")
        self.FM.folder_handler_multiple([['Picture', 'output'],['Record','output'],['Record','converted']],['picture_output','record_output', 'record_converted'])
        tm.sleep(1)

    def picture(self):
        name = 'image_{}.jpg'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('picture_output')
        file_path_name = os.path.join(path, name)
        self.camera.capture(file_path_name)
        return file_path_name

    def record(self):
        self.camera.resolution = (640, 480)
        self.camera.start_recording('1.h264')
        self.camera.wait_recording(5)
        
        i = 0
        while True:
            i =+ 1
            self.camera.split_recording("Loop{}.mp4".format(i))
            self.camera.wait_recording(5)
            if i > 2:
                break
        
        self.camera.stop_recording()
    
    def convert_h264_mp4(self, file_name):
        file_mp4 = os.path.splitext(file_name)[0] + ".mp4"
        command = "ffmpeg -i " + file_name + " " + file_mp4
        call([command], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return file_mp4

    def file(self):
        name = 'video_{}.h264'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('record_output')
        file_path_name = os.path.join(path, name)
        
        self.camera.resolution = (640, 480)
        self.camera.start_recording(file_path_name)
        self.camera.wait_recording(15)
        self.camera.stop_recording()

        return file_path_name
    
    def video(self):
        name = 'video_{}.h264'.format(dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        path = self.FM.get_folder('record_output')
        file_path_name = os.path.join(path, name)
        print(file_path_name)
        
        self.camera.resolution = (640, 480)
        self.camera.start_recording(file_path_name)
        self.camera.wait_recording(5)
        self.camera.stop_recording()

        return self.convert_h264_mp4(file_path_name)        


if __name__ == '__main__':
    run = Camera()
    run.video()
    # run.FM.deep_clean_folder('picture_output')
    # run.FM.deep_clean_folder('record_output')
    
        