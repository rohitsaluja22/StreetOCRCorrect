import cv2
import argparse, json, math, os
import numpy as np
from collections import defaultdict
import os, sys
import configparser
from time import sleep
from tkinter import ttk
import threading
import time
import requests
import ujson as json
import time
import platform
import numpy as np
import argparse
import io
import base64
from PIL import Image
from collections import OrderedDict
base_path = os.path.dirname(os.path.abspath(__file__))
def arg_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file', type=str, help='input video file name')
	parser.add_argument('--Rotate180Flag', type=int, help='make it 1 if you want to rotate video by 180 degree')
	return parser.parse_args()

class VideoGen:

	def __init__(self,video_file, Rotate180F):
		self.filename = video_file
		self.Rotate180Fl = Rotate180F
		self.filename_prefix = os.path.splitext(video_file)[0]
		self.json_file = self.filename_prefix + '_bboxdata.json' 
		self.json_file_rev = self.filename_prefix + '_bboxdata_rev.json'

		self.cap = cv2.VideoCapture(video_file)
		# for iterating on video file frame wise
		self.data = self.parse_json(self.json_file) # self.data[frame_no][id] gives [x,y,w,h]
		# for easy retrieval of metadata summary like max width|height of bboxes per id
		self.data_rev = self.parse_json(self.json_file_rev) # self.data_rev[id][frame_no] gives [x,y,w,h]
		self.metadata = {}
		self.vid_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
		self.video_writer_instances = {}
		self.maxDict = {}
		self.suggDict = {}

	def parse_json(self,filename):
		with open(filename, 'r') as fp:
			data = json.load(fp)
		return data

	def parse_metadata_from_json(self):
		# This will find max width & height per ID and store it for later use
		for ID, level_2_dict in self.data_rev.items():
			max_width = 0
			max_height = 0
			for frame_no, bbox in level_2_dict.items():
				x,y,w,h = bbox
				if w > max_width:
					max_width = w
				if h > max_height:
					max_height = h
			self.metadata[ID] = [int(max_width),int(max_height)]

	def video_writer_init(self,ID):
		width,height = (self.maxDict[ID][2] - self.maxDict[ID][0]), (self.maxDict[ID][3] - self.maxDict[ID][1])
		os.makedirs(self.filename_prefix,exist_ok=True)
		#os.makedirs(self.filename_prefix+"_images",exist_ok=True)
		vid_name = ("%05i" % int(ID)) + ".avi"
		outfile = os.path.join(self.filename_prefix,vid_name)
		fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
		#print(outfile, 0, self.vid_fps, (width,height))
		video = cv2.VideoWriter(outfile, fourcc, self.vid_fps, (width,height))
		return video

	def get_video_writer_instance(self,ID):
		video = self.video_writer_instances.get(ID)
		if video is None:
			video = self.video_writer_init(ID)
			self.video_writer_instances[ID] = video
		return video
	def get_maxboundary(self):
		#maxDict
		frames = list(self.data.keys())
		for frame_count in range(int(frames[-1])):
			#print(frame_count, int(frames[-1]))
			id_bbox_data = self.data.get(str(frame_count))
			if id_bbox_data is None:
				continue
			#print("id_bbox_data",id_bbox_data)
			for ID, bbox in id_bbox_data.items():
				x,y,w,h = bbox
				if ID not in self.maxDict:
					self.maxDict[ID] = [x, y, x+w, y+h]
				else:
					self.maxDict[ID] = [min(x,self.maxDict[ID][0]), min(y,self.maxDict[ID][1]), max(x+w,self.maxDict[ID][2]), max(y+h,self.maxDict[ID][3])]
				
	def test_model(self,img,x, y, w, h):
		rows = img.shape[0]
		cols = img.shape[1]
		new_x = min(x,rows-1) if x > 0 else 0
		new_y = min(y,cols-1) if y > 0 else 0

		new_h = min(int(1.15*h), rows-1)
		new_w = min(int(1.05*w), cols-1)

		model_h = 260
		model_w = 480

		h_aspect = int((new_w*model_h)/model_w)

		if h_aspect < new_h:
			temp = new_y + (new_h - h_aspect)
			new_y = min(rows-1, temp)
		else:
			temp = new_y - (h_aspect - new_h)
			new_y = max(0, temp)

		new_h = h_aspect

		# crop image
		crop_img = img[new_y:new_y+new_h, new_x:new_x+new_w]

		# convert to Bytes using Pillow and BytesIO
		#pil_crop = Image.fromarray(crop_img)
		#inpByteArr = io.BytesIO()
		#pil_crop.save("cropped.png", format='PNG')
		#imgpred = open("cropped.png", 'rb').read()
		#print(imgpred.type())
		_,imagedata = cv2.imencode('.PNG',crop_img)
		imgpred1 = base64.b64encode(imagedata).decode("ascii")
		#inpByteArr = inpByteArr.getvalue()
		#cv2.imshow('image',img)
		#cv2.waitKey(0)
		endpoint = 'predict_debug'
		PORT = 5000
		url = 'http://localhost:%d/'%(PORT) + endpoint # Neeti server URL

		#fname = '.'.join(os.path.basename(img_path).split('.')[:-1])
		#if img is None:
		#	img = open(img_path, 'rb').read()
	
		#name = "model_files/"+fname # if saving scores on server side: scores_data/$name/fname
		files = {'img':imagedata, 'frame_no':"", 'index':str(0), 'mask':json.dumps({})}
		a = time.time()

		rdata = requests.request('post', url = url, files=files)
		b = time.time() - a

		if platform.system() == 'Windows' or True:
			r = json.loads(rdata.json())
		else:
			r = rdata.json()

		text = r.get('text','[]')
		score1 = r.get('score1','[]')
		#print(score1)
		conf = 1
		for i in score1[0]:#.split("], [")[0].replace("[","").split(","):
			conf = conf*(i)/100
		return 	text.split("', '")[0].replace("[\'",""), conf		

	def generate_id_wise_video(self):
		frame_count = 0
		
		frames = list(self.data.keys()) # list of strings
		
		width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float
		height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float
		self.get_maxboundary()
		while(self.cap.isOpened()):
			ret, imgcv = self.cap.read()
			if(self.Rotate180Fl): imgcv = cv2.flip(imgcv, -1 )
			if not ret or frame_count==int(frames[-1]):# or frame_count > 5:
				break
			id_bbox_data = self.data.get(str(frame_count))
			#print(frame_count)
			if id_bbox_data is None:
				frame_count+=1
				continue
			for ID, bbox in id_bbox_data.items():
				video_writer = self.get_video_writer_instance(ID)
				x,y,w,h = bbox
				conf = 0
				pred, conf = self.test_model(imgcv,x,y,w,h)
				if (conf < 0.001) or (conf is None) : continue#TO DO REVIEW THIS LOGIC
				if int(ID) not in self.suggDict:
					#print("here1")
					self.suggDict[int(ID)] = {}
				if pred not in self.suggDict[int(ID)]:
					#print("here2")
					self.suggDict[int(ID)][pred] = 0
				self.suggDict[int(ID)][pred] += 1
				#print(self.suggDict)
				#print(ID ,pred, conf)
				#imgcv[y,x:x+w] = 0
				#imgcv[y+h,x:x+w] = 0
				#imgcv[y:y+h,x] = 0
				#imgcv[y:y+h,x+w] = 0
				'''max_width, max_height = self.metadata[ID]
				
				# blank_image = np.zeros((max_height,max_width,3), np.uint8)
				x_offset = (max_width - w)//2
				y_offset = (max_height - h)//2
				

				# crop
				x1 = max(0, x - x_offset)
				x2 = min(x1 + max_width, width)
				y1 = max(0, y - y_offset)
				y2 = min(y1 + max_height, height)

				crop = imgcv[y1:y2,x1:x2].copy()'''


				x1, y1, x2, y2 = tuple(self.maxDict[ID])
				crop = imgcv[y1:y2,x1:x2].copy()

				# print(x1,x2,y1,y2)
				# print(crop.shape)

				blur = cv2.GaussianBlur(crop.copy(),(21,21),0)
				blur[y-y1:y-y1+h,x-x1:x-x1+w] = crop[y-y1:y-y1+h,x-x1:x-x1+w]
				#uncomment/comment for box in video
				#blur[y-y1:y-y1+h,x-x1] = 0
				#blur[y-y1:y-y1+h,x-x1+w] = 0
				#blur[y-y1,x-x1:x-x1+w] = 0
				#blur[y-y1+h,x-x1:x-x1+w] = 0
				#print(frame_count, blur.shape)
				#cv2.imwrite(os.path.join(self.filename_prefix+"_images",ID+"_"+str(frame_count)+".jpg"),blur)
				video_writer.write(blur)
			if frame_count % 25 == 0:
				active_ids = list(id_bbox_data.keys())
				all_ids = self.video_writer_instances.keys()
				# used list() because we're popping keys at realtime and want the list to be static
				for ID in list(self.video_writer_instances.keys()):
					if ID not in active_ids:
						video_writer = self.video_writer_instances.pop(ID,None)
						if video_writer:
							video_writer.release()
			frame_count += 1
		# used list() because we're popping keys at realtime and want the list to be static
		#print("self.suggDict", self.suggDict)
		#print("self.suggDict Sorted", sorted(self.suggDict))
		for id in sorted(self.suggDict):
			#print("self.suggDict Inside", self.suggDict[id])
			dd = sorted(self.suggDict[id].items(),key = lambda index:index[1])
			#print(id, dd)
			dd.reverse()
			ddSorted = OrderedDict(dd)
			self.suggDict[id] = ddSorted
			listSorted = list(ddSorted.keys())
			#base_path + "/" + self.filename_prefix + "/"+ 
			print(("%05i" % id)+".avi\t"+"\t".join(listSorted))
		for ID in list(self.video_writer_instances.keys()):
			video_writer = self.video_writer_instances.pop(ID,None)
			if video_writer:
				video_writer.release()

args = arg_parser()

video_gen = VideoGen(args.file,args.Rotate180Flag)
video_gen.parse_metadata_from_json()
video_gen.generate_id_wise_video()
