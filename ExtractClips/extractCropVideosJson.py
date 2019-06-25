import numpy as np
import cv2, time, os
import json, time
from threading import Thread
from collections import defaultdict
import sys
from pydarknet import Detector, Image

class Analyse:
	def __init__(self):
		self.options = {"model": "cfg/yolov3.cfg", "load": "weights/yolov3.weights", "threshold": 0.1, "gpu":0.9}
		self.net = Detector(bytes("cfg/yolov3.cfg", encoding="utf-8"),
			bytes("weights/yolov3.weights", encoding="utf-8"), 0,
			bytes("cfg/coco.data",encoding="utf-8"))
		self.json_results = {}
		self.l = []    #l = [vehicals(None,None,None,None)]
		self.NUMBER_VEHICLE = 1
		self.uniquename = None
		self.data = defaultdict(lambda: defaultdict(list)) # bhavya: will store bbox for every id for every frame
		# self.data[frame_no][id] gives [x,y,w,h]
		self.data_rev = defaultdict(lambda: defaultdict(list)) # bhavya: data but with keys inverted
		# self.data_rev[id][frame_no] gives [x,y,w,h]

	# bbox_format = (x,y,w,h)
	class vehicals:
		def __init__(self, Id, bbox,tracker,init):
			self.ID = Id
			self.bbox = bbox
			self.tracker = tracker
			self.init = init
			self.labels = []
			self.crop = False

	# bbox argument = [x1,y1,x2,y2]
	def add_bbox(self,ID, bbox):
		print("addingbbox", bbox)
		# global l, self.NUMBER_VEHICLE
		bbox = (bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1])
		tracker = cv2.TrackerMedianFlow_create() #cv2.TrackerGOTURN_create() #cv2.TrackerKCF_create()##cv2.TrackerCSRT_create()#   # cv2.TrackerMedianFlow_create()
		init = False
		p = self.vehicals(ID, bbox,tracker,init)
		self.l.append(p)
		self.NUMBER_VEHICLE += 1

	def del_bbox(self,ID):
		i= 0
		for obj in self.l:
			if obj.ID == ID:
				self.json_results[obj.ID] = obj.labels
				# print(self.json_results)
				#"1":[[ct,"hel",0.5],[2,"no",12]],
				'''fw = open("uploads/json_results.txt","a")#/"+self.uniquename+
				if len(obj.labels)>5:
					print('"'+str(obj.ID)+'":'+json.dumps(obj.labels)+",",file=fw)
				fw.close()'''
				del self.l[i]
				break
			i = i +1

	def init_frame(self,frame=None):
		global FRAME
		self.remove_overlapping_boxes()
		for obj in self.l:
			x1 = obj.bbox[0]
			x2 = obj.bbox[0]+obj.bbox[2]
			y1 = obj.bbox[1]
			y2 = obj.bbox[1]+obj.bbox[3]
			# print("\n\n\n Init deletion ",x1,y1,x2,y2)
			# if y1<100 or y2>650 or x1<50 or x2>1220:
			#     del_bbox(obj.ID)
			if obj.init == False:
				if frame is not None:
					obj.tracker.init(frame, obj.bbox)
					FRAME = frame
				else:
					obj.tracker.init(FRAME, obj.bbox)
				obj.init = True

	### use of this function????
	def update_bbox(self,ID,bbox,vidwidth,vidheight):
		global FRAME
		bbox = (bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1])
		for obj in self.l:
			if obj.ID == ID:
				# print("something")
				obj.bbox = bbox
				obj.tracker.init(FRAME, obj.bbox)
				if bbox[1] <= 100:
					self.del_bbox(obj.ID)
				elif bbox[1]+bbox[3] >= vidheight-100:
					self.del_bbox(obj.ID)
				elif bbox[0] <= 100:
					self.del_bbox(obj.ID)
				elif bbox[0]+bbox[2] >= vidwidth-120:
					self.del_bbox(obj.ID)
				# if obj.speed>50:
				#     del_bbox(obj.ID)
				break

	# returns [x1,y1,x2,y2,id]
	def track(self,frame):
		global FRAME
		FRAME = frame
		bboxes = []
		for obj in self.l:
			success, bbox = obj.tracker.update(frame)
			if success:
				obj.bbox = bbox
			box = obj.bbox
			box = [int(box[0]),int(box[1]),int(box[2]+box[0]),int(box[3]+box[1]),obj.ID]
			bboxes.append(box)
		return bboxes

	def remove_overlapping_boxes(self):
		delIDs = []
		for i in range(len(self.l)):
			obj1 = self.l[i]
			boxA = [obj1.bbox[0], obj1.bbox[1],obj1.bbox[0]+obj1.bbox[2], obj1.bbox[1]+obj1.bbox[3]]
			for j in range(i+1,len(self.l)):
				obj2 = self.l[j]
				boxB = [obj2.bbox[0], obj2.bbox[1],obj2.bbox[0]+obj2.bbox[2], obj2.bbox[1]+obj2.bbox[3]]
				iou = self.bb_intersection_over_union(boxA, boxB)
				if iou > 0.3:
					delIDs += [obj2.ID]
		for id in delIDs:
			self.del_bbox(id)


	def bb_intersection_over_union(self,boxA, boxB):
		xA = max(boxA[0], boxB[0])
		yA = max(boxA[1], boxB[1])
		xB = min(boxA[2], boxB[2])
		yB = min(boxA[3], boxB[3])
		interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
		boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
		boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
		if interArea/boxAArea == 1 or interArea/boxBArea == 1:
			iou = 1
		else:
			iou = interArea / float(boxAArea + boxBArea - interArea)
		return iou

	def write_to_json_file(self,filename_prefix):
		import json
		with open(filename_prefix+'_bboxdata.json', 'w') as fp:
			json.dump(self.data, fp, sort_keys=True, indent=4)
		with open(filename_prefix+'_bboxdata_rev.json', 'w') as fp:
			json.dump(self.data_rev, fp, sort_keys=True, indent=4)


	def main_func(self,filename, Rotate180Flag):
		begin = time.time()
		total_time, yolo_time, classifier_time, number_of_images_classified, tracker_time = 0,0,0,0,0
		self.uniquename = filename.split(".")[0]
		filename_prefix = os.path.splitext(filename)[0]
		cap = cv2.VideoCapture(filename)

		####### commenting out code - start
		# def tflite_threading(res, i, content):
		# 	score = self.aml.classify(content)
		# 	res[i] = ["nohelmet",score]
		# 	return True
		####### commenting out code - end

		count = 0
		start = time.time()
		length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		fps = int(cap.get(cv2.CAP_PROP_FPS))

		fw = open("uploads"+"json_results.txt","w")#+self.uniquename
		fw.write('"fps":'+str(fps)+",")
		fw.close()

		while(cap.isOpened()):
			ret, imgcv = cap.read()
			if(Rotate180Flag): imgcv = cv2.flip(imgcv, -1 )
			if imgcv is not None:
				vidheight, vidwidth, ch = imgcv.shape
			#print("vidheight, vidwidth",vidheight, vidwidth)
			if not ret or count==2000:
				break
			print(count)
			if count==0 or count%10==0:
				ys = time.time()
				img_darknet = Image(imgcv)
				results = self.net.detect(img_darknet)
				#print(results)
				print("yolo time taken: ",time.time()-ys)
				yolo_time += (time.time()-ys)

				ts = time.time()
				for cat, score, bounds in results:
					# print(box["label"])
					label = str(cat.decode("utf-8"))
					x,y,w,h = bounds
					x,y,w,h = int(x),int(y),int(w),int(h)
					#print(label)
					if label in ["car","motorbike","bus","truck"]:
						x1,y1,x2,y2 = x-w//2,y-h//2,x+w//2,y+h//2
						id = int(self.NUMBER_VEHICLE)
						if (x2-x1)>50 and (y2-y1)>50 and x1>100 and x2<vidwidth-120 and y1>100 and y2<vidheight-100:
							bbox = [x1,y1,x2,y2]
							bbox = [max(0,x1),max(y1,0),min(vidwidth-1,x2),min(vidheight-1,y2)]
							print("bboxcarbikebus",bbox)
							self.add_bbox(id,bbox)
							'''#Comment out to store yolo images
							imgcv[y1,x1:x2] = 0
							imgcv[y2,x1:x2] = 0
							imgcv[y1:y2,x1] = 0
							imgcv[y1:y2,x2] = 0
							cv2.imwrite(os.path.join("yoloimages/",str(count)+".jpg"),imgcv)'''
				self.init_frame(imgcv)
				print("Tracker time taken1: ",time.time()-ts)
				tracker_time += (time.time()-ts)

			else:
				ts = time.time()
				bboxs = self.track(imgcv)
				#print(bboxs)
				for boxes in bboxs:
					Id = boxes[4]
					bb = [max(0,boxes[0]),max(boxes[1],0),min(vidwidth-1,boxes[2]),min(vidheight-1,boxes[3])]
					self.update_bbox(Id,bb,vidwidth,vidheight)
				print("Tracker time taken: ", time.time()-ts)
				yolo_time += (time.time()-ts)

			for obj in self.l:
				ID = obj.ID
				# print(count,obj.bbox)
				self.data[count][ID] = obj.bbox
				self.data_rev[ID][count] = obj.bbox
			count += 1
		self.write_to_json_file(filename_prefix)


		while len(self.l):
				self.del_bbox(self.l[0].ID)
		cap.release()
		total_time = time.time()-begin
		print("Total time = ", total_time)
		print("\nYolo time = ", yolo_time)
		print("\nTracker time = ", tracker_time)


if (len(sys.argv) < 2): print("USAGE: python3 extractCropVideosJson.py <video_name.mp4> Rotate180Flag")
else: 
	anl = Analyse()
	Rotate180Flag = 1
	if len(sys.argv) == 2: Rotate180Flag = 0
	if len(sys.argv) == 3: Rotate180Flag = int(sys.argv[2])
	print("Rotate180Flag",Rotate180Flag)
	ans = anl.main_func(sys.argv[1], Rotate180Flag)
