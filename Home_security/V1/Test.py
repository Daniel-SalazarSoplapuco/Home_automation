from time import sleep
import subprocess


def convert(file_h264, file_mp4):
    # Convert the h264 format to the mp4 format.
    command = "ffmpeg -i " + file_h264 + " " + file_mp4
    subprocess.run([command], 
    stdout=DEVNULL, 
    stderr=subprocess.STDOUT)
    print("\r\nRasp_Pi => Video Converted! \r\n")
        

# Record a video and convert it (MP4).
convert("/home/uf829d/python_projects/program_files/Camera/Record/output/video_2021-03-21_16-21-13.h264", "/home/uf829d/python_projects/program_files/Camera/Record/output/video_2021-03-21_16-21-13.mp4")