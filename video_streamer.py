import PIL
from PIL import Image, ImageTk
# import Tkinter as tk
from tkinter import OptionMenu,StringVar,Entry,Scrollbar
from tkinter.tix import ScrolledWindow
import tkinter as tk
import argparse
import datetime
import cv2
import os
import random
import threading
import sys
import time
import os
import configparser
from base_class import *
import ast

class Application(Skeleton):

	def __init__(self):
		""" Initialize application which uses OpenCV + Tkinter. It displays
			a video stream in a Tkinter window and stores current snapshot on disk """
		super().__init__()
		self.get_config() # retrieve configuration
		self.set_video_details() # set video details as per video file
		self.scale = float(self.config['VIDEO']['scale'].strip())
		self.ms_per_frame =  int(self.config['PLAYBACK_CONTROLS']['ms_duration_video_loop']) # milliseconds per video loop
		self.playback_speed = 1 # = how many times to read frame consecutively (i.e. skip n - 1 frames)
		# self.output_path = os.getcwd()  # store output path
		self.current_image = None  # current image from the camera
		self.masks = ast.literal_eval(self.config['VIDEO']['masking'])
		self.values = []
		self.root = tk.Tk()  # initialize root window
		#self.scrollbar = Scrollbar(self.root)
		#self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.frame0 = tk.Frame(self.root);self.frame1 = tk.Frame(self.root);
		self.frame2 = tk.Frame(self.root);self.frame3 = tk.Frame(self.root)
		self.frame4 = tk.Frame(self.root);
		self.frame5 = tk.Frame(self.root);
		self.frame6 = tk.Frame(self.root);
		self.frame7 = tk.Frame(self.root);
		self.frame8 = tk.Frame(self.root);
		self.frame9 = tk.Frame(self.root);
		self.frame10 = tk.Frame(self.root);
		#self.scrollbar.config(command=self.yview)
		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()
		if self.screen_width<1280 and self.screen_height<1080:
			self.root.geometry('%sx%s' % (self.screen_width, self.screen_height))
		else:
			self.root.geometry('1280x1080')
		self.root.title("Test")  # set window title
		# self.destructor function gets fired when the window is closed
		self.root.protocol('WM_DELETE_WINDOW', self.destructor)

		self.frames_info = tk.Label(self.frame0)
		self.speed_slider = tk.Scale(self.frame0, label='Slide right to speed up playback',
			orient = 'horizontal', from_=1, to=5, command=self.set_speed, length=200)
		#self.help_button = tk.Button(self.frame0, text="Help",command = lambda: self.popup(self.config['HELP']['text']))

		self.panel = tk.Label(self.frame1)  # initialize image panel
		self.panel.config(width=int(self.vid_width/self.scale),height=int(self.vid_height/self.scale))
		# self.panel.bind("<Button-1>",self.mouse_click)

		pc = self.config['PLAYBACK_CONTROLS']
		kc = self.config['KEYBOARD_CONTROLS']
		for i in kc.keys():
			kc[i] = kc[i].upper()
		self.pause_play = tk.Button(self.frame2, text="| |/▷(Ctrl+%s)"%kc['key_pause_play'],command = self.mouse_click)
		self.rewind_button2 = tk.Button(self.frame2, text="<<< %ss (Ctrl+%s)"%(pc['rewind_duration'],kc['key_rewind_1']),
			command = lambda: self.rewind(float(pc['rewind_duration'])))
		self.rewind_button1 = tk.Button(self.frame2, text="< 0.1s (Ctrl+%s)"%kc['key_rewind_2'],
			command = lambda: self.rewind(0.1))
		self.forward_button1 = tk.Button(self.frame2, text="> 0.1s (Ctrl+%s)"%kc['key_forward_2'],
			command = lambda: self.forward(0.1))
		self.forward_button2 = tk.Button(self.frame2, text=">>> %ss (Ctrl+%s)"%(pc['forward_duration'],kc['key_forward_1']),
			command = lambda: self.forward(float(pc['forward_duration'])))
		self.next_button = tk.Button(self.frame2, text="-->> nextfile (Ctrl+%s)"%kc['key_next'],
			command = lambda: (self.nextfile(),self.nextfile2()))
		self.discard_button = tk.Button(self.frame2, text="✂ Undo Last", command = self.discard_last_annotation)

		self.entry = tk.Button(self.frame4, text="Entry (Ctrl+%s)"%kc['key_entry'])
		self.entry.config(command = lambda: self.record_entry())
		self.OPTIONS = ["MH 04 HM 9246", "MH 04 HM 9346", "MH 04 HH 9226",
							"HH 04 HH 9226", "KK 03 HH 9226"]

		self.variable = StringVar(self.root)
		#self.w = OptionMenu(self.frame5, self.variable, *self.OPTIONS)

		self.variable.set(self.OPTIONS[0])
		self.variable.trace('w', callback=self.callback)
		self.variable2 = StringVar(self.root, value=self.variable.get())
		self.v1 = StringVar(self.root)
		self.v2 = StringVar(self.root)
		self.v3 = StringVar(self.root)
		self.v4 = StringVar(self.root)
		self.v5 = StringVar(self.root)
		self.text_box = Entry(self.frame5, textvariable=self.v1)
		self.text_box.bind("<Tab>", self.focus_next_window)

		self.text_box2 = Entry(self.frame6, textvariable=self.v2)
		self.text_box2.bind("<Tab>", self.focus_next_window)
		self.submit_box2 = tk.Button(self.frame6, text="Submit (Ctrl+%s)" % kc['key_submit'],
									command=lambda: self.submit(self.text_box2))

		self.text_box3 = Entry(self.frame7, textvariable=self.v3)
		self.text_box3.bind("<Tab>", self.focus_next_window)
		self.submit_box3 = tk.Button(self.frame7, text="Submit (Ctrl+%s)" % kc['key_submit'],
									command=lambda: self.submit(self.text_box3))
		self.text_box4 = Entry(self.frame8, textvariable=self.v4)
		self.text_box4.bind("<Tab>", self.focus_next_window)
		self.submit_box4 = tk.Button(self.frame8, text="Submit (Ctrl+%s)" % kc['key_submit'],
									command=lambda: self.submit(self.text_box4))
		self.text_box5 = Entry(self.frame9, textvariable=self.v5)
		self.text_box5.bind("<Tab>", self.focus_next_window)
		self.submit_box5 = tk.Button(self.frame9, text="Submit (Ctrl+%s)" % kc['key_submit'],
									command=lambda: self.submit(self.text_box5))


		self.values = []
		self.values.append(self.v1)
		self.values.append(self.v2)
		self.values.append(self.v3)
		self.values.append(self.v4)
		self.values.append(self.v5)

		for i in range(0,self.sendSuggestions.__len__()):
			if i > 4:
				break
			self.values[i].set(self.sendSuggestions[i])
		#self.w.bind("<Tab>", self.focus_next_window)
		#self.entry.bind("<Return>",la4bda event: self.text_box.focus_set())
		#self.entry.bind("<Tab>",lambda event: self.text_box.focus_set())
		# self.text_box.focus_set()
		self.exit = tk.Button(self.frame4, text="Exit (Ctrl+%s)"%kc['key_exit'])
		self.exit.config(command = lambda: self.record_exit())
		self.submit_box = tk.Button(self.frame5, text="Submit (Ctrl+%s)"%kc['key_submit'], command= lambda: self.submit(self.text_box))
		self.reset_box = tk.Button(self.frame4, text="Reset", command= lambda: self.reset())

		self.frames_info.pack(side=tk.LEFT)
		self.speed_slider.pack(side=tk.RIGHT, padx = 10)
		#self.help_button.pack(side=tk.LEFT)

		self.pause_play.pack(side=tk.LEFT)
		self.rewind_button2.pack(side=tk.LEFT)
		self.rewind_button1.pack(side=tk.LEFT)
		# self.rewind_button3.pack(side=tk.LEFT)
		self.forward_button1.pack(side=tk.LEFT)
		self.next_button.pack(side=tk.LEFT)
		self.forward_button2.pack(side=tk.LEFT)
		self.discard_button.pack(side=tk.LEFT)

		self.entry.pack(side=tk.LEFT, padx=10)
		self.text_box.pack(side=tk.LEFT, padx=10)
		self.text_box2.pack(side=tk.LEFT, padx=10)
		self.text_box3.pack(side=tk.LEFT, padx=10)
		self.text_box4.pack(side=tk.LEFT, padx=10)
		self.text_box5.pack(side=tk.LEFT, padx=10)
		#self.w.pack(side=tk.LEFT, padx=10)
		self.exit.pack(side=tk.LEFT, padx=10)
		self.submit_box.pack(side=tk.LEFT, padx=10)
		self.submit_box2.pack(side=tk.LEFT, padx=10)
		self.submit_box3.pack(side=tk.LEFT, padx=10)
		self.submit_box4.pack(side=tk.LEFT, padx=10)
		self.submit_box5.pack(side=tk.LEFT, padx=10)
		
		self.reset_box.pack(side=tk.LEFT, padx=10)

		self.panel.pack(padx=10, pady=10)
		self.frame0.pack(padx=10, pady=10);self.frame1.pack(padx=10, pady=10);
		self.frame2.pack(padx=10, pady=10);#self.frame3.pack(padx=10, pady=10)
		self.frame4.pack(padx=10, pady=10)
		self.frame5.pack(padx=10, pady=10)
		self.frame6.pack(padx=10, pady=10)
		self.frame7.pack(padx=10, pady=10)
		self.frame8.pack(padx=10, pady=10)
		self.frame9.pack(padx=10, pady=10)
		self.frame10.pack(padx=10, pady=10)
		self.root.config(cursor="arrow")
		self.root.bind("<Return>",lambda event: self.root.focus_get().invoke())
		self.bind_keys()

		restore_ID, restore_frame = self.get_last_annotated_frame()
		self.ID = restore_ID + 1
		print("Restoring ID to: %d"%self.ID)
		print("%s, ON ID:%d"%(self.get_localtime(),self.ID), file=self.f_time_log, flush=True)
		print("S.No.\tFile Name\t\t\t\t\tAnnotation\tFrom\tTo",file=self.f,flush=True)
		self.reset()
		self.vs.set(cv2.CAP_PROP_POS_FRAMES, restore_frame)
		self.frame_no = restore_frame
		# create a button, that when pressed, will take the current frame and save it to file
		# btn = tk.Button(self.root, text="Snapshot!", command=self.take_snapshot)
		# btn.pack(fill="both", expand=True, padx=10, pady=10)

		# start a self.video_loop that constantly pools the video sensor
		# for the most recently read frame
		self.video_loop()

	def nextfile2(self):
		#self.nextfile()
		for i in range(0,self.sendSuggestions.__len__()):
			if i > 4:
				break
			self.values[i].set(self.sendSuggestions[i])
		#self.video_loop()

	def callback(self,*args):
		print("changed")
		'''self.varible2 = StringVar(self.root, value=self.variable.get())
		self.text_box.setvar(name=textvariable,value = self.variable2.get())
		self.text_box.setvar()
		self.text_box.setvar()'''
		print(self.variable2.get())

	def loop_once(self):
		ok, self.frame = self.vs.read()
		if ok:  # frame captured without any errors
			# key = cv2.waitKey(1000)
			cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)  # convert colors from BGR to RGBA
			cv2resized = cv2.resize(cv2image,fx = 1/self.scale,fy = 1/self.scale,dsize = (0,0))
			self.current_image = Image.fromarray(cv2resized)  # convert image for PIL
			#self.current_image= self.current_image.resize([1280,1024],PIL.Image.ANTIALIAS)
			imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
			self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector
			self.panel.config(image=imgtk)  # show the image
			#self.panel2.bind("<Button-1>",callback)
			#self.root.attributes("-fullscreen",True)
			self.frame_no+=1

	def Suggestor(self,frameInstance):
		suggesstions = ["MH 04 HM 9246", "MH 04 HM 9346", "MH 04 HH 9226",
							"HH 04 HH 9226", "KK 03 HH 9226","AB 04 CD 9226","EF 04 GH 9226","IJ 04 KL 9226","MN 04 OP 9226","QR 04 ST 9226","MH 04 HH 9226"]
		k = random.randrange(0, suggesstions.__len__(),1)
		#time.sleep(2)
		for i in range(0,10000000):
			pass
		return suggesstions[k]

	def video_loop(self):
		speed = self.playback_speed
		is_entry = self.is_entry
		is_exit = self.is_exit
		""" Get frame from the video stream and show it in Tkinter """
		# self.frames_remaining.text=str(self.length-self.frame_no)
		#self.frames_info.config(text="""Frames finished: %d Frames left: %d Annotated Vehicles so far: %d Entry frame: %s Exit frame: %s"""%(self.frame_no-1,self.length-self.frame_no+1,self.ID-1,self.frame_e,self.frame_x))
		self.frames_info.config(text="""Annotated Vehicles so far: %d Entry frame: %s Exit frame: %s"""%(self.ID-1,self.frame_e,self.frame_x))
		#count = 1
		##self.vs = cv2.VideoCapture(os.path.join(get_application_path(), self.filename)) ## PLEASE SEE THIS COMMENT
		if not self.is_paused:
		#	count = count + 1
			ok, self.frame = self.vs.read()  # read frame from video stream
			#print("current frame is:",self.frame)
			#if(count%100==0):
			#self.v1.set(self.Suggestor(self.frame))
			#time.sleep(2)
			if ok:
				self.frame_no+=1
				cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)  # convert colors from BGR to RGBA
			# if is_entry and not is_exit:
			# 	self.collected_frames.append([self.frame_no,cv2image])
			# skip frames for speed up
			for i in range(speed - 1):
				ok, self.frame = self.vs.read()
				if ok:
					self.frame_no+=1
					cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
				# if is_entry and not is_exit:
					# self.collected_frames.append([self.frame_no+i+1,cv2image])
			if ok:
				# frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
				# frame = cv2.resize(frame, (1280,520))
				for mask in self.masks:
					x,y,w,h = mask
					cv2image[y:y+h,x:x+w,:] = 0
				cv2resized = cv2.resize(cv2image,fx = 1/self.scale,fy = 1/self.scale,dsize = (0,0))
				# print(type(cv2image))
				if ok:  # frame captured without any errors
					# key = cv2.waitKey(1000)
					
					self.current_image = Image.fromarray(cv2resized)  # convert image for PIL
					#self.current_image= self.current_image.resize([1280,1024],PIL.Image.ANTIALIAS)
					imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
					self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector  
					self.panel.config(image=imgtk)  # show the image
					#self.panel.bind("<Button-1>",callback)
					#self.root.attributes("-fullscreen",True)
				
				# self.video_loop()
		focused_widget = self.root.focus_get()
		# if focused_widget == self.text_box and self.binded:
		# 	print("Unbinding Keys")
		# 	self.unbind_keys()
		# elif focused_widget != self.text_box and not self.binded:
		# 	print("Binding Keys")
		# 	self.bind_keys()
		self.root.after(self.ms_per_frame, self.video_loop)  # call the same function after n milliseconds

	# def take_snapshot(self):
	#     """ Take snapshot and save it to the file """
	#     ts = datetime.datetime.now() # grab the current timestamp
	#     filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))  # construct filename
	#     p = os.path.join(self.output_path, filename)  # construct output path
	#     self.current_image.save(p, "JPEG")  # save image as jpeg file
	#     print("[INFO] saved {}".format(filename))

	# Submit button
	def submit(self,text_box):
		if self.submit_box["state"] == tk.DISABLED:
			return
		corrected_text = self.filename+"\t"+text_box.get().replace(" ","")#self.variable.get().replace(" ","")
		#check = self.frame_e <= self.frame_x
		start = self.frame_e
		end = self.frame_x
		if corrected_text != '': #and self.frame_e is not None and self.frame_x is not None and check:
			if (self.frame_e is None):
				start = 1# and (self.frame_x is None)):
				#data = [str(self.ID),corrected_text,str(1),str(int(self.length))]#self.length-3)]
			if (self.frame_x is None):
				end = int(self.length)
			if(end<start):
				end = int(self.length)
			data = [str(self.ID),corrected_text,str(start),str(end)]
			self.last_annotation = data
			self.log_list.append(data)
			string = "\t".join(data)
			print(string,file=self.f,flush=True)
			self.ID += 1
			print("%s, SUBMIT ID:%d"%(self.get_localtime(),self.ID), file=self.f_time_log, flush=True)
		else:
			if corrected_text == '':
				self.popup("Error: Text Box is empty")
		# print("Collected Frames:",len(self.collected_frames),"Annotated Frames:",self.frame_x-self.frame_e+1)
		# print("Collected Start Frame:",self.collected_frames[0][0],"Annotated Start Frame:",self.frame_e)
		# print("Collected End Frame:",self.collected_frames[-1][0],"Annotated End Frame:",self.frame_x)
		self.reset(goto_last_annot=False) # reset boxes
		self.is_paused = False

	# reset annotation boxes like text box, and bottons
	def reset(self,goto_last_annot=True):
		#self.text_box.delete('1.0',tk.END)
		#self.text_box.pack()
		t = threading.Timer(0.5, self.reset_button,[("entry",self.entry),("exit",self.exit)])
		t.start()
		self.is_entry = False
		self.is_exit = False
		self.frame_e = None; self.frame_x = None;
		last_annotated_frame_end = 0
		last_annotated_frame_end = int(self.last_annotation[END_FRAME_IDX]) if self.last_annotation != [] else 0 #This was givng error du
		if goto_last_annot:
			self.frame_no = last_annotated_frame_end
			self.vs.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
		if self.is_paused:
			self.loop_once()
		self.collected_frames = []

	def bind_keys(self):
		#a = self.root.bind("z",self.mouse_click)
		keyboard_config = kc = self.config['KEYBOARD_CONTROLS']
		pc = self.config['PLAYBACK_CONTROLS']
		x = lambda x: x.strip()
		key_pairs = [[x(kc['key_pause_play']),self.mouse_click],
			[x(kc['key_entry']),lambda x: self.record_entry()],
			[x(kc['key_exit']),lambda x: self.record_exit()],
			[x(kc['key_submit']),lambda x: self.submit()],
			[x(kc['key_rewind_1']),lambda x: self.rewind(float(pc['rewind_duration']))],
			[x(kc['key_forward_1']),lambda x: self.forward(float(pc['forward_duration']))],
			[x(kc['key_rewind_2']),lambda x: self.rewind(0.1)],
			[x(kc['key_forward_2']),lambda x: self.forward(0.1)],
			[x(kc['key_next']),lambda x: self.nextfile()],
		]
		# alphabets + numericals
		self.bindings = []
		for key,bind_func in key_pairs:
			print("Binding Control-"+key.upper(),"to",bind_func.__name__)
			if key.isdigit():
				a = self.root.bind("<Control-"+key+">",bind_func)
			else:
				a = self.root.bind("<Control-"+key.lower()+">",bind_func)
				b = self.root.bind("<Control-"+key.upper()+">",bind_func)	
		# p = self.root.bind("Z",self.mouse_click)
		# b = self.root.bind("E",lambda x: self.record_entry())
		# c = self.root.bind("X",lambda x: self.record_exit())
		# d = self.root.bind("R",lambda x: self.rewind(2))
		# e = self.root.bind("F",lambda x: self.forward(2))
		# f = self.root.bind("S",lambda x: self.submit())
		# _9 = self.root.bind("9",lambda x: self.rewind(0.1))
		# _0 = self.root.bind("0",lambda x: self.forward(0.1))
		# self.bindings = [("E",b),("X",c),("R",d),("F",e),("S",f),("9",_9),("0",_0),("z",p)]
		self.binded = True

	def unbind_keys(self):
		for key,bindid in self.bindings:
			self.root.unbind(key,bindid)
		self.binded = False

	def focus_next_window(self,event):
		event.widget.tk_focusNext().focus()
		return("break")

	def destructor(self):
		""" Destroy the root object and release all resources """
		print("[INFO] closing...")
		self.root.destroy()
		self.vs.release()  # release web camera
		# for i in self.log_list:
		# 	string = "\t".join(i)
		# 	print(string,file=self.f)
		print("%s, OFF ID:%d"%(self.get_localtime(),self.ID), file=self.f_time_log, flush=True)
		self.f.close()
		self.f_deleted.close()
		self.f_time_log.close()
		# cv2.destroyAllWindows()  # it is not mandatory in this application



# construct the argument parse and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-o", "--output", default=path + "/",
#     help="path to output directory to store snapshots (default: current folder")
# args = vars(ap.parse_args())

# start the app
print("[INFO] starting...")
pba = Application()        #Application(args["output"])
pba.root.mainloop()
