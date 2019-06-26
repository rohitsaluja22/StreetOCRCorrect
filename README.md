# StreetOCRCorrect

# Demo
The demo video of the backend model used in our framework is available here: https://drive.google.com/open?id=1xetAEINYOlS-HUgFj71DRMtdr8FMVBtc


# Module1: Steps to Extract Multiple Single Vehicle Video Clips:

# Installations (Tested on Ubuntu 16.04 with 4GB GeForce 940MX):
On python 3.6, install opencv and pydarknet from https://pypi.org/project/yolo34py/ i.e.:-
```
sudo apt-get update
sudo apt-get install python3.6
#use "virtualenv -p python3.6 StreetOCR" if using virtual environment
pip3 install opencv-python
pip3 install opencv_contrib-python # For MedianFlow Tracker
pip3 install numpy
pip3 install yolo34py-gpu
pip3 install ujson
pip3 install PILLOW
cd ExtractClips
```

download weights and config files: https://github.com/madhawav/YOLO3-4-Py/blob/master/download_models.sh
folder structure should be as follows:
```
ExtractClips/cfg/coco.data
ExtractClips/cfg/yolov3.cfg
ExtractClips/weights/yolov3.weights
ExtractClips/data/coco.names
```

Download and host ANPR API:-
```
Download this google drive folder https://drive.google.com/open?id=1ywfwJPlHf9wfqqkAX6HKq-CI46WZbinB
#Open a new tab with Ctrl+Shift+Tab
chmod +x StreetOCRDemo/ANPR_UbuntuDemo
./StreetOCRDemo/ANPR_UbuntuDemo #note that you might need to bypass proxy to run this
```
Optional: Download and trim youtube video:-
```
Download one of the videos with highest resolution given in downloadYoutubeChaoticVideos
Best video to try demo is https://www.youtube.com/watch?v=77MpjKvOgz0
rename the downloaded video as 001.mp4

#For try the demo on 5 secs of video:-
avconv -i 001.mp4 -ss 00:00:06 -t 00:00:05 -codec copy input.mp4 
#(Ignore if you want to run on complete video) 
```

# Usage for Module1 for extracting single vehicle clips via Detection and Tracking on Demo Video:
```
Come back to ExtractClips folder in older (or a new) tab, and move the demo mp4 file from StreetOCRDemo/ to ExtractClips/:-
cd ExtractClips
mv StreetOCRDemo/StreetOCRDemoVideo.mp4 .
python3 extractCropVideosJson.py StreetOCRDemoVideo.mp4 1
# make last term 0 or omit it if you DO NOT want to rotate video by 180 degrees while reading

python3 parse_json_videogen.py --file StreetOCRDemoVideo.mp4 --Rotate180Flag 1 > Suggestions.txt
# make Rotate180Flag as 0 if you DO NOT want to rotate video by 180 degrees while reading/writing
cp Suggestions ../../StreetOCRCorrect
```
The above steps will extract and store single vehicle clips in a new folder "ExtractClips/StreetOCRDemoVideo". The same are also present in StreetOCRDemo/StreetOCRDemoVideoSingleVehicleClips to match (or check in case you are not able to run this).
The next Module takes "Suggestions" generated in ExtractClips/. Make sure you have copied Suggestions.txt to folder "StreetOCRCorrect/"

# Module2: Using StreetOCRCorrect

1. In params.cfg: 
	(a) only edit the folder name, it should be relative or absolute w.r.t the exe.
	   EXAMPLE: folder_name = ExtractClips/StreetOCRDemoVideo/
	(b) Increase scale to reduce window size or decrease scale to increase window size	
```
cd ..
python3 video_streamer.py
```
2. To annotate license plate for 1 vehicle, process is straightforward
	(a) Press start button when vehicle enters the frame
	(b) Annotate the vehicle
	(c) By default entry is 1st frame of the clip and exit is last frame of the clip.
	(d) If license plate is not visible/readable at the entry of a vehicle in the clip, then you can press entry
	button from the point where license plate is visible and readable.
	(e) Press exit button at the last frame with visible and readable license plate.
	(f) Verify/edit the best suggestion out of the 5 (or less) suggestions shown and click Submit button to the 
	right of the suggestion that you choose.
3. Click Next Video or Ctrl+N to load the next video in UI.
4. You can fast forward the video playback speed using the slider above.
5. You can pause/play the video by clicking on the video frame or use Ctrl+Z. You can do that to pause and annotate when fast forwarding. 
	Click once: Video will be paused
	Click again: Video will resume
6. You can rewind a video by 5, 10 or 15 seconds at a time.
	NOTE: if you rewind a video to the point where a previously 
	annotated car is ENTERING the frame, you will have to
	annotate such cars again from that point.
7. To skip/reset a submission after clicking start and end frames, submit an empty annotation. The system will ignore and reset buttons.
8. To override start position again on an already green button, click on the button again to register an update before clicking.
9. Video will start after the last annotated vehicle from the logs.
10. Keep code and .cfg file both, in same folder
11. Do not delete or modify the log files that are generated.
