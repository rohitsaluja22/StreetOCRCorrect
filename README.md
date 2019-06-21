# StreetOCRCorrect

# Demo
The demo video of the backend model used in our framework is available here: https://drive.google.com/open?id=1xetAEINYOlS-HUgFj71DRMtdr8FMVBtc

# Using StreetOCRCorrect
1. In params.cfg: only edit the video file name, it should be relative or absolute w.r.t the exe.
	 EXAMPLE1: file_name = video_name.mp4
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
