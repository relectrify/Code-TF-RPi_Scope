import visa
import sys
from rigol import ds1000z
import logging
import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import boto3
import time
import datetime
import uuid
import csv
from random import randint
from shutil import copyfile

def raw_data_to_string(raw_data):
    string = str(raw_data).strip("b\'").strip("\\ne")
    string = string.replace(',', '\n')
    return string

class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
    
    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class ScopeCapture(QWidget):
    def __init__(self, parent = None):
        super(ScopeCapture, self).__init__(parent)
        
        # rm = visa.ResourceManager('@py')
        # resources = rm.list_resources()
        # usb = list(filter(lambda x: 'USB' in x, resources))
        # device = rm.open_resource(usb[0])
        # device.timeout = None
        # self.scope = ds1000z.Ds1000z(device)

        self.s3 = boto3.resource('s3')
        self.myBucket = self.s3.Bucket('relectrify-tools-oscilloscopedata')

        self.cb = QComboBox()
        self.cb.addItems(["Alice","Bob","Charlie"])

        self.pb = QPushButton('Capture')
        self.pb.clicked.connect(self.on_pb_clicked)

        self.listOfButtons = []
        self.pbChOne = self.setup_button("1")
        self.pbChOne.clicked.connect(lambda: self.on_btn_clicked(self.pbChOne))
        self.pbChTwo = self.setup_button("2")
        self.pbChTwo.clicked.connect(lambda: self.on_btn_clicked(self.pbChTwo))
        self.pbChThree = self.setup_button("3")
        self.pbChThree.clicked.connect(lambda: self.on_btn_clicked(self.pbChThree))
        self.pbChFour = self.setup_button("4")
        self.pbChFour.clicked.connect(lambda: self.on_btn_clicked(self.pbChFour))

        logTextBox = QPlainTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.INFO)

        hbox = QHBoxLayout()
        hbox.addWidget(self.cb)
        hbox.addWidget(self.pb)

        channelHBox = QHBoxLayout()
        channelHBox.addWidget(self.pbChOne)
        channelHBox.addWidget(self.pbChTwo)
        channelHBox.addWidget(self.pbChThree)
        channelHBox.addWidget(self.pbChFour)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(channelHBox)
        vbox.addWidget(logTextBox.widget)

        self.setLayout(vbox)

        self.setWindowTitle("Scope Capture")
        self.resize(480,600)
        qtRect = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRect.moveCenter(centerPoint)
        self.move(qtRect.topLeft())
    
    def setup_button(self, name):
        self.btn = QPushButton(name)
        self.btn.setCheckable(True)
        return self.btn
    
    def on_btn_clicked(self, btn):
        if btn in self.listOfButtons:
            self.listOfButtons.remove(btn)
            print("Removed button {}".format(btn.text()))
        else:
            self.listOfButtons.append(btn)
            print("Added button {}".format(btn.text()))

    def setup_data_file(self,filename):
        with open(filename, 'w') as f:
            f.write("Time\n")
            for i in range(1,1201):
                f.write(str(i)+"\n")

    def append_csv(self,myfile,tmpfile,item,data):
        with open(myfile, 'r') as csvinput:
            with open(tmpfile, 'w') as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n')
                reader = csv.reader(csvinput)
                all = []
                row = next(reader)
                row.append("Ch {}".format(item.text()))
                all.append(row)
                for row in reader:
                    # print(int(row[0]))
                    row.append(data[int(row[0])-1])
                    all.append(row)
                writer.writerows(all)

    def on_pb_clicked(self):
        myfile = 'test.csv'
        tmpfile = 'temp.csv'
        self.setup_data_file(myfile)
        for item in self.listOfButtons:
            # data = [randint(0,9) for x in range(1,1201)]
            data = self.scope.get_data()
            self.append_csv(myfile,tmpfile,item,data)
            copyfile(tmpfile,myfile)
        print("clicked pb")
        return
        waveform = raw_data_to_string(self.scope.get_data())
        print(waveform)
        filename = "_"+str(self.cb.currentText())+"_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = self.createTempFile(filename)
        with open(filename+".csv", 'w') as f:
            for point in waveform:
                f.write(point)
        try:
            self.myBucket.put_object(Key=filename+'.csv', Body=open(filename+'.csv', 'rb'))
            logging.info("successfully uploaded "+filename+".csv")
        except:
            logging.info("something went wrong uploading csv")
        
        self.scope.get_screenshot(filename+".png")
        try:
            self.myBucket.put_object(Key=filename+'.png', Body=open(filename+'.png', 'rb'))
            logging.info("successfully uploaded "+filename+".png")
        except:
            logging.info("something went wrong uploading png")
        

    def createTempFile(self, file_name):
        return ''.join([str(uuid.uuid4().hex[:6]), file_name])

def main():
    app = QApplication([])
    ex = ScopeCapture()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()