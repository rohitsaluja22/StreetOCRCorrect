import os, sys
import cv2
import configparser
from time import sleep
import tkinter as tk
from tkinter import ttk , StringVar
import threading
import time
from os import listdir
from os.path import isfile, join
import random
from collections import Counter

# indexes
ID_IDX,ANNOT_IDX,START_FRAME_IDX,END_FRAME_IDX = [0,1,2,3]

def get_application_path():
	if getattr(sys, 'frozen', False):
		application_path = os.path.dirname(sys.executable)
	elif __file__:
		application_path = os.path.dirname(__file__)
	return application_path

class Skeleton():

	def __init__(self):
		self.frame_no = 0
		self.frame_e = 0
		self.frame_x = 0
		self.is_paused = False
		self.filename = ""
		self.filename_pref = ""
		self.scale = None # scale is in inverse ratio. 2 means = 1/2 (half) scaling of video
		self.fps = 0
		self.length = 0
		self.vs = None
		self.output_path = ""
		self.is_entry = False 
		self.is_exit = False
		self.config = None # config file
		self.collected_frames = []
		self.last_annotation = []
		self.ID = 1 # future ID of annotation
		self.FirstVideoFlag = 1
		# keyboard shortcuts
		self.key_pause_play = self.key_entry = self.key_exit = self.key_rewind_1 = self.key_forward_1 = None
		self.key_submit = self.key_rewind_2 = self.key_forward_2 = self.key_Next = None
		self.onlyfiles = []
		self.fileIndent = 0
		self.sendSuggestions = []
		self.suggestions = {}


	# will set all video details and initialize video capture stream
	def set_video_details(self):
		mypath = self.config['INPUT']['folder_name'].strip()
		#print(mypath)
		if(self.FirstVideoFlag):
			#self.onlyfiles = [f for f in listdir(mypath) if (isfile(join(mypath, f)) and (not (f.split(".")[-1] == "txt")))]
			#self.FirstVideoFlag = 0
			self.onlyfiles = list(sorted(self.suggestions.keys())
		self.filename = mypath + self.onlyfiles[self.fileIndent]
		print(self.filename)
		self.filename_pref, ext = os.path.splitext(self.filename)

		self.vs = cv2.VideoCapture(os.path.join(get_application_path(),self.filename)) # capture video frames, 0 is your default video camera

		#print(s1)
		#print(sugg)
		self.fps = self.vs.get(cv2.CAP_PROP_FPS)
		self.vid_width = int(self.vs.get(cv2.CAP_PROP_FRAME_WIDTH))
		self.vid_height = int(self.vs.get(cv2.CAP_PROP_FRAME_HEIGHT))
		self.frame_no = 0
		print("fps:",self.fps)
		self.length = self.vs.get(cv2.CAP_PROP_FRAME_COUNT)
		print("length:",self.length)
		if self.fps == float('Inf') :
			print("FPS is %f. Setting fps as 25."%self.fps)
			self.fps = 25
		if self.length == float('Inf') or self.length <= 0:
			print("Frame Count is %f. Setting FL as 90000."%self.length)
			self.length = 90000
		self.fps = int(self.fps)
		self.length = int(self.length)
		ok, self.frame = self.vs.read()
		self.length = self.vs.get(cv2.CAP_PROP_FRAME_COUNT)
		self.sendSuggestions = self.suggestions[self.onlyfiles[self.fileIndent]]
		#print(self.sendSuggestions)
		'''ma = (int)(self.length / 20)
		count = 1
		s1 = []
		while (self.frame is not None):
			ok, self.frame = self.vs.read()
			if (count % ma == 0):
				k = random.randrange(0, suggesstions.__len__(), 1)
				s1.append(suggesstions[k])
			count = count + 1
		coun = Counter(s1)
		sugg = coun.most_common(5)
		self.sendSuggestions = []
		for ltter, count in sugg:
			self.sendSuggestions.append(ltter)
		print("Suggestion:",self.sendSuggestions)'''
		# os.makedirs(self.filename_pref,exist_ok=True)

	def get_config(self):
		path = os.getcwd()
		self.config = configparser.ConfigParser()
		# filename = sys.argv[1].split('.')[0]
		self.config.read(os.path.join(get_application_path(), 'params.cfg'))
		sList = [line.rstrip('\n') for line in open(path+"/Suggestions.txt", 'r')]
		#print(sList)
		for x in sList:
			x1 = x.split("\t")
			self.suggestions[x1[0]] = x1[1:]
		#print(self.suggestions)


	def discard_last_annotation(self):
		self.is_paused = True
		line = self.delete_last_line()
		self.f.flush()
		line2 = self.delete_last_line(delete=False)
		self.last_annotation = line2.strip().split()
		print("LINE1:",line)
		print("LINE2:",line2)
		print("ID was: %d"%self.ID)
		if line.strip() == '':
			self.ID = 1
			self.vs.set(cv2.CAP_PROP_POS_FRAMES, 0)
			self.frame_no = 0
			print("ID is: %d"%self.ID)
		else:
			print("%s, DISCARD ID:%s"%(self.get_localtime(),line.strip().split()[0]), file=self.f_time_log, flush=True)
			print(line,file=self.f_deleted,flush=True) # logging into separate file
			if line2.strip() == '':
				self.ID = 1
				self.vs.set(cv2.CAP_PROP_POS_FRAMES, 0)
				self.frame_no = 0
				print("ID is: %d"%self.ID)
			else:
				ID,annot,start,end=line2.strip().split()
				restore_frame = int(end)
				self.vs.set(cv2.CAP_PROP_POS_FRAMES, restore_frame)
				self.frame_no = restore_frame
				self.ID = int(ID) + 1
				print("ID is: %d"%self.ID)
		self.is_paused = False

	# returns the last line. If delete =True, then it also deletes it
	def delete_last_line(self,delete=True):
		# https://stackoverflow.com/a/10289740
		file = self.f
		#Move the pointer (similar to a cursor in a text editor) to the end of the file. 
		file.seek(0, os.SEEK_END)
		#This code means the following code skips the very last character in the file - 
		#i.e. in the case the last line is null we delete the last line 
		#and the penultimate one
		if sys.platform == 'win32': # For Windows 32 and 64 bit
			pos = file.tell() - 2
			char = file.read(1)
			char = file.read(1)
		elif sys.platform == 'linux':
			pos = file.tell() - 1
		elif sys.platform == 'darwin':
			pos = file.tell() - 1 # TODO: Fix the number for this with trial and error
		#Read each character in the file one at a time from the penultimate 
		#character going backwards, searching for a newline character
		#If we find a new line, exit the search
		line = ""
		#char = file.read(1)
		#char = file.read(1)
		char = file.read(1)
		# char = file.read(1)
		print("POS:",pos)
		while pos > 0:
			if char == "\n":
				break
			line += char
			pos -= 1
			file.seek(pos, os.SEEK_SET)
			char = file.read(1)
		if pos == 0:
			line += char
		#So long as we're not at the start of the file, delete all the characters ahead of this position
		if delete:
			if pos>0:
				file.seek(pos+1, os.SEEK_SET)
				file.truncate()
			elif pos==0:
			 	file.seek(pos, os.SEEK_SET)
			 	file.truncate()
		else:
			file.seek(0,os.SEEK_END)
		return line[::-1] # returning the reverse of the line, since SEEK operates in reverse

	def get_last_annotated_frame(self):

		self.f = open(os.path.join(get_application_path(),'log.txt'),'a+')
		self.f_deleted = open(os.path.join(get_application_path(),'deleted_log.txt'),'a+')
		self.f_time_log = open(os.path.join(get_application_path(),'log_t.txt'),'a+')
		self.log_list = []
		# restore frame from logs
		self.f.seek(0)
		lines = self.f.readlines()[1:]
		restore_frame = int(lines[-1].split("\t")[END_FRAME_IDX]) if lines != [] else 0
		if(restore_frame >= self.length):
			restore_frame = 0
		restore_ID = int(lines[-1].split("\t")[ID_IDX]) if lines != [] else 0
		self.last_annotation = lines[-1].split() if lines != [] else []

		return restore_ID,restore_frame

	def record_entry(self):
		if self.entry["state"] == tk.DISABLED:
			return
		self.entry.config(bg='green',activebackground='green')
		self.frame_e = self.frame_no - 1
		self.is_entry = True
		print("%s, ENTRY VEHICLE CALLBACK"%(self.get_localtime()), file=self.f_time_log, flush=True)
		self.exit["state"] = tk.NORMAL
		self.text_box.focus_set()
		self.collected_frames = []

	def record_exit(self):
		if self.exit["state"] == tk.DISABLED:
			return
		self.exit.config(bg='green',activebackground='green')
		self.frame_x = self.frame_no - 1
		self.is_exit = True
		print("%s, EXIT VEHICLE CALLBACK"%(self.get_localtime()), file=self.f_time_log, flush=True)
		#self.entry["state"] = tk.DISABLED
		self.submit_box["state"] = tk.NORMAL
		# self.collected_frames.append([self.frame_no,self.frame])

	def reset_button(self,*args):
		# default colour
		for name,button in args:
			if name == "entry":
				button["state"] = tk.NORMAL
			if name == "exit":
				button["state"] = tk.NORMAL
			button.config(bg='#d9d9d9',activebackground='#d9d9d9')
		self.submit_box["state"] = tk.NORMAL

	def get_localtime(self):
		localtime = time.asctime( time.localtime(time.time()))
		return localtime

	def mouse_click(self,event=None):
		self.is_paused = not self.is_paused
		print("%s, Pause Mode: %s"%(self.get_localtime(),self.is_paused), file=self.f_time_log, flush=True)
		print("Toggling Pause Mode to",self.is_paused)

	def rewind(self, seconds):
		last_annotated_frame_end = int(self.last_annotation[END_FRAME_IDX]) if self.last_annotation != [] else 0
		# subtracting 1 for looping once which will consume 1 frame
		# if frame_e is None:
		self.frame_no = max(self.frame_no - int(seconds*self.fps) - 1, last_annotated_frame_end)
		# frames_list = [entry[0] for entry in self.log_list]
		# print(self.log_list[-1][1])
		# while self.log_list != []:
		# 	if self.frame_no < int(self.log_list[-1][1]):
		# 		self.log_list.pop()
		# 	else:
		# 		break
		self.set_box_states()
		self.vs.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
		print("<< Rewind %0.1fs <<"%seconds)
		print("%s, Rewind %0.1fs"%(self.get_localtime(),seconds), file=self.f_time_log, flush=True)
		if self.is_paused:
			self.loop_once()

	def set_box_states(self):
		if self.frame_e is not None and self.frame_x is None:
			if self.frame_no < self.frame_e:
				self.frame_e = None
				t = threading.Timer(0.2, self.reset_button,[("entry",self.entry),("exit",self.exit)])
				t.start()
		if self.frame_e is not None and self.frame_x is not None:
			if self.frame_no < self.frame_e:
				self.frame_e = None
				self.frame_x = None
				t = threading.Timer(0.2, self.reset_button,[("entry",self.entry),("exit",self.exit)])
				t.start()
			elif self.frame_no < self.frame_x:
				self.frame_x = None
				for name,button in [("entry",self.entry),("exit",self.exit)]:
					if name == "entry":
						button["state"] = tk.DISABLED
					if name == "exit":
						button["state"] = tk.NORMAL
						button.config(bg='#d9d9d9',activebackground='#d9d9d9')
				self.submit_box["state"] = tk.NORMAL

	def nextfile(self):
		self.fileIndent = (self.fileIndent + 1) % len(self.onlyfiles)
		#if len(filenameTemp) > self.filename: self.filename = self.filename.split("/")[0] + "/" + 
		self.set_video_details()
		print(self.filename)

	def forward(self, seconds):
		# subtracting 1 for looping once which will consume 1 frame
		self.frame_no = min(self.frame_no + int(seconds*self.fps) - 1, self.length)
		self.vs.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
		print("%s, Forward %0.1fs"%(self.get_localtime(),seconds), file=self.f_time_log, flush=True)
		if self.is_paused:
			self.loop_once()

	def set_speed(self,val):
		self.playback_speed = int(val)
		print("Playback Speed is: %dx"%self.playback_speed)

	def popup(self,text=""):
		win = tk.Toplevel()
		win.wm_title("Error")
		# win.protocol('WM_DELETE_WINDOW', lambda: self.remove_tmp(win))

		text_label = tk.Label(win,text=text)
		f1 = tk.Frame(win)
		# l.grid(row=0, column=0)

		#self.annot_text_box.grid(row=0, column=1)
		win.bind('<Return>',win.destroy)
		okay_button = ttk.Button(f1, text="OK", command= win.destroy)
		#b.grid(row=1, column=0, sticky="ew")
		text_label.pack(side = tk.TOP, fill = "both", expand = "yes")
		f1.pack();okay_button.pack()
		self.center(win)

	# centering annotation popup on screen
	def center(self,win):
		"""
		centers a tkinter window
		:param win: the root or Toplevel window to center
		"""
		win.update_idletasks()
		width = win.winfo_width()
		frm_width = win.winfo_rootx() - win.winfo_x()
		win_width = width + 2 * frm_width
		height = win.winfo_height()
		titlebar_height = win.winfo_rooty() - win.winfo_y()
		win_height = height + titlebar_height + frm_width
		x = win.winfo_screenwidth() // 2 - win_width // 2
		y = win.winfo_screenheight() // 2 - win_height // 2
		win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
		# win.geometry('{}x{}+{}+{}'.format(int(width*2), height//2, x, y))
		win.deiconify()
