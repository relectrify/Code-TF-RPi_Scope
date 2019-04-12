import time
from rigol.rigol_ds1054z import rigol_ds1054z
from tkinter import *
import boto3

class Window(Frame):
	def __init__(self, master=None):
		Frame.__init__(self, master)
		self.master = master
		self.init_window()
		self.init_osc()
		self.init_s3()

	def init_osc(self):
		try:
			self.osc = rigol_ds1054z()
			self.osc.print_info()
		except IndexError:
			print("Device not connected.")
		except Exception:
			print("Resource is busy.")

	def capture_waveforms(self):
		for i in range(1,5):
			if self.osc.channel_enabled(channel=i):
				self.osc.write_waveform_data(channel=i,filename="test.csv")
	
	def init_s3(self):
		self.s3 = boto3.resource('s3')
		self.myBucket = self.s3.Bucket('relectrify-tools-oscilloscopedata')
	
	def upload_to_s3(self, file):
		try:
			self.myBucket.put_object(Key=file, Body=open(file, 'rb'))
		except:
			print("Something went wrong uploading file to S3")

	def init_window(self):
		self.master.title("Rigol Oscilloscope Capture")
		self.pack(fill=BOTH, expand=1)
		captureButton = Button(self, text="Capture",command=self.capture_and_upload)
		captureButton.place(relx=0.5, rely=0.5, anchor=CENTER)
		initOscButton = Button(self, text="Reconnect",command=self.init_osc)
		initOscButton.place(relx=0.0, rely=0.0, anchor=NW)

	def capture_and_upload(self):
		self.capture_waveforms()	

def main():
	root = Tk()
	root.geometry("400x300")	
	app = Window(root)
	root.mainloop()

if __name__ == "__main__":
	main()
