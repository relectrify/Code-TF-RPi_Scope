import time
from rigol.rigol_ds1054z import rigol_ds1054z
from tkinter import *
import boto3
from boto3.s3.transfer import TransferConfig 
import csv
from shutil import copyfile
import uuid
import datetime
import os
import sys
import threading

class ProgressPercentage(object):
	def __init__(self, filename):
		self._filename = filename
		self._size = float(os.path.getsize(filename))
		self._seen_so_far = 0
		self._lock = threading.Lock()	
	
	def __call__(self, bytes_amount):
		with self._lock:
			self._seen_so_far += bytes_amount
			percentage = (self._seen_so_far / self._size) * 100
			sys.stdout.write(
				"\r%s / %s (%.2f%%)" % (
					self._seen_so_far, self._size, percentage))
			sys.stdout.flush()

class Window(Frame):
	def __init__(self, master=None):
		Frame.__init__(self, master)
		self.master = master
		self.init_window()
		self.connected = False
		self.init_osc()
		self.init_s3()

	def init_osc(self):
		if self.connected:
			self.osc.close()
			self.labelVar.set("Device not connected")
			self.buttonVar.set("Connect")
			self.connected = False
		else:
			try:
				self.osc = rigol_ds1054z()
				self.osc.print_info()
				self.osc.setup_mem_depth(memory_depth=6e6)
				self.labelVar.set("Device connected")
				self.buttonVar.set("Disconnect")
				self.connected = True
			except IndexError:
				self.labelVar.set("Device not connected")
				self.buttonVar.set("Connect")
			except Exception:
				print("Resource is busy.")

	def append_data_to_file(self, channel_num, data, filename):
		with open(filename, 'r') as csvinput:
			with open("temp_"+filename, 'w') as csvoutput:
				writer = csv.writer(csvoutput, lineterminator='\n')
				reader = csv.reader(csvinput)
				all = []
				row = next(reader)
				row.append("Ch"+str(channel_num))
				all.append(row)
				for row in reader:
					row.append(data[int(row[0])-1])
					all.append(row)
				writer.writerows(all)
		copyfile("temp_"+filename, filename)

	def capture_waveforms(self, filename):
		with open(filename, 'w') as f:
			f.write("Count\n")
			for i in range(1,462001):
				f.write(str(i)+"\n")

		for i in range(1,5):
			if self.osc.channel_enabled(channel=i):
				data = self.osc.write_waveform_data(channel=i)
				self.append_data_to_file(i, data, filename)

		os.remove("temp_"+filename)
	
	def capture_screenshot(self, filename):
		self.osc.write_screen_capture(filename)

	def init_s3(self):
		self.s3 = boto3.resource('s3')
		self.myBucket = self.s3.Bucket('relectrify-tools-oscilloscopedata')
	
	def multi_part_upload_with_s3(self, file):
		config = TransferConfig(multipart_threshold=1024 * 25,
					max_concurrency=10,
					multipart_chunksize=1024 * 25,
					use_threads=True)
		file_path=os.path.join(os.getcwd(),file)
		bucket = 'relectrify-tools-oscilloscopedata'
		key_path = file
		try:
			self.s3.meta.client.upload_file(Filename=file_path, Bucket=bucket, Key=key_path, Config=config, Callback=ProgressPercentage(file_path))
			os.remove(file)
			print("\nSuccessfully uploaded {} to S3".format(file))
		except:
			print("\nSomething went wrong uploading {} to S3".format(file))

	def init_window(self):
		self.master.title("Rigol Oscilloscope Capture")
		self.pack(fill=BOTH, expand=1)
	
		self.labelVar = StringVar()
		self.deviceText = Label(self, textvariable=self.labelVar)
		self.deviceText.place(relx=0.0, rely=0.0, anchor=NW)

		captureButton = Button(self, text="Capture",command=self.capture_and_upload)
		captureButton.place(relx=0.5, rely=0.5, anchor=CENTER)

		self.buttonVar = StringVar()
		initOscButton = Button(self, textvariable=self.buttonVar,command=self.init_osc)
		initOscButton.place(relx=0.5, rely=0.0, anchor=N)

	def capture_and_upload(self):
		filename_root = ''.join([str(uuid.uuid4().hex[:6]), "_", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")])

		csv_file = filename_root + ".csv"	
		self.capture_waveforms(csv_file)	

		png_file = filename_root + ".png"
		self.capture_screenshot(png_file)

		self.multi_part_upload_with_s3(csv_file)
		self.multi_part_upload_with_s3(png_file)

def main():
	root = Tk()
	root.geometry("400x300")	
	app = Window(root)
	root.mainloop()

if __name__ == "__main__":
	main()
