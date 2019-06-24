# StreetOCRCorrect

# Demo
The demo video of the backend model used in our framework is available here: https://drive.google.com/open?id=1xetAEINYOlS-HUgFj71DRMtdr8FMVBtc


# Module1: Steps to Extract Multiple Single Vehicle Video Clips:

# Installations (Tested on Ubuntu 16.04 with 4GB GeForce 940MX):
install opencv and pydarknet from https://pypi.org/project/yolo34py/ i.e.:-
```
pip3 install opencv-python
pip3 install opencv_contrib-python # For MedianFlow Tracker
pip3 install numpy
pip3 install yolo34py-gpu
cd ExtractClips
```

download weights and config files: https://github.com/madhawav/YOLO3-4-Py/blob/master/download_models.sh
folder structure should be as follows:
ExtractClips/cfg/coco.data
ExtractClips/cfg/yolov3.cfg
ExtractClips/weights/yolov3.weights
ExtractClips/data/coco.names

Download and trim input video:-
```
Download one of the video with youtube-dl or any youtube downloader (make sure you download highest quality version for better results)
rename the downloaded video as 001.mp4
avconv -i 001.mp4 -ss 00:01:27 -t 00:00:5 -codec copy input.mp4 # (Ignore if you want to run on complete video) 
```

# Usage for Module1:
```
#ffmpeg -i input.mp4 -c copy -metadata:s:v:0 rotate=180 input1.mp4 # use this in case your video is inverted
python3 extractCropVideosJson.py input.mp4
python3 parse_json_videogen.py --file input.mp4 
```
The above steps will store vehicle clips in a new folder "input", you will have to filter the clips where license plates are not readable manually or ignore them while using the Module 2 (given below). We are working on improving this part by using confidence scores from our License Plate Recognition Models.

# Module2: Using StreetOCRCorrect
cd ..
1. In params.cfg: only edit the folder name, it should be relative or absolute w.r.t the exe.
	 EXAMPLE1: folder_name = ExtractClips/input/
2. To annotate for 1 vehicle, process is straightforward
	a. Press start button when vehicle enters the frame
	b. Annotate the vehicle
	c. Press exit button when the vehicle exits the frame so that exit frame is captured.
	d. Submit
3. You can fast forward the video playback speed using the slider above.
4. You can pause/play the video by clicking on the video frame. You can do that to pause and annotate when fast forwarding. 
	Click once: Video will be paused
	Click again: Video will resume
5. You can rewind a video by 5, 10 or 15 seconds at a time.
	NOTE: if you rewind a video to the point where a previously 
	annotated car is ENTERING the frame, you will have to
	annotate such cars again from that point.
6. To skip/reset a submission after clicking start and end frames, submit an empty annotation. The system will ignore and reset buttons.
7. To override start position again on an already green button, click on the button again to register an update before clicking.
8. Video will start after the last annotated vehicle from the logs.
9. Keep exe/code and .cfg file both, in same folder
10. DO NOT DELETE OR MODIFY THE LOG FILES THAT ARE GENERATED.
