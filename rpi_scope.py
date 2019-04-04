import visa
from rigol import ds1000z
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

def raw_data_to_string(raw_data):
    string = str(raw_data).strip("b\'").strip("\\ne")
    string = string.replace(',', '\n')
    return string

class ScopeCapture(QWidget):
    def __init__(self, parent = None):
        super(ScopeCapture, self).__init__(parent)
        
        resources = visa.ResourceManager('@py').list_resources()
        usb = list(filter(lambda x: 'USB' in x, resources))
        device = rm.open_resource(usb[0])
        device.timeout = None
        self.scope = ds1000z.Ds1000z(device)

        self.cb = QComboBox()
        self.cb.addItems(["Alice","Bob","Charlie"])
        self.cb.currentIndexChanged.connect(self.selectionchange)

        self.pb = QPushButton('Capture')
        self.pb.clicked.connect(self.on_pb_clicked)

        logTextBox = QPlainTextEditLogger(self)
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

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

    def test(self):
        logging.debug('damn, a bug')
        logging.info('something to remember')
        logging.warning('that\'s not right')
        logging.error('foobar')

    def on_pb_clicked(self):
        self.scope.get_screenshot("test.png")
        waveform = raw_data_to_string(self.scope.get_data())
        with open("waveform.csv", 'w') as f:
            for point in waveform:
                f.write(point)

    def selectionchange(self, i):
        print("Current index {}".format(self.cb.itemText(i)))

def main():
    app = QApplication([])
    ex = scopeCapture()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()