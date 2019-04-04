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
        
        rm = visa.ResourceManager('@py')
        resources = rm.list_resources()
        usb = list(filter(lambda x: 'USB' in x, resources))
        device = rm.open_resource(usb[0])
        device.timeout = None
        self.scope = ds1000z.Ds1000z(device)

        self.s3 = boto3.resource('s3')
        self.myBucket = self.s3.Bucket('relectrify-tools-oscilloscopedata')

        self.cb = QComboBox()
        self.cb.addItems(["Alice","Bob","Charlie"])

        self.pb = QPushButton('Capture')
        self.pb.clicked.connect(self.on_pb_clicked)

        logTextBox = QPlainTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.INFO)

        hbox = QHBoxLayout()
        hbox.addWidget(self.cb)
        hbox.addWidget(self.pb)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(logTextBox.widget)

        self.setLayout(vbox)

        self.setWindowTitle("Scope Capture")
        self.resize(480,600)
        qtRect = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRect.moveCenter(centerPoint)
        self.move(qtRect.topLeft())

    def on_pb_clicked(self):
        waveform = raw_data_to_string(self.scope.get_data())
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