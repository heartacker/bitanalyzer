#!/usr/bin/env python3.9
#encoding=utf-8
import os,json,re,sys
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QScrollArea, \
    QApplication
from ui import *

CFG = {"version" : "1.0", "bcolor" : "#55ffff", "language" : "English" }
LG = {
    "app_name": ["BitAnalyzer", "比特分析器"],
    "color"   : ["color", "颜色"],
    "left"    : ["left", "左移"],
    "right"   : ["right", "右移"],
    "MSB"     : ["MSB", "高位"],
    "clear"   : ["clear", "清空"],
    "ones"    : ["1 numbers", "1数量"],
    "sub"     : ["sub", "段"],
    "newpanel": ["new panel", "新面板"],
    "help"    : ["help", "帮助"],
    "about"   : ["about", "关于"],
    "guide"   : ["guide", "使用说明"],
    "language": ["language", "语言"]
}

class MAIN_UI(QMainWindow):
    def __init__(self, panel="standard", hex_value=""):
        super(MAIN_UI, self).__init__()
        if os.path.exists("config.json"):
            try:
                with open("config.json", 'r') as cfg_file:
                    cfgs = json.load(cfg_file)
                    if "version"  in cfgs: CFG["version"]  = cfgs["version"]
                    if "bcolor"   in cfgs: CFG["bcolor"]   = cfgs["bcolor"]
                    if "language" in cfgs: CFG["language"] = cfgs["language"]
            except:
                os.remove("config.json")

        lg = 0 if CFG["language"]=="English" else 1

        titl_str = (LG["app_name"][lg]+" V"+CFG["version"]) if panel=="standard" else panel
        self.setWindowTitle(titl_str)
        self.setWindowIcon(QIcon(os.path.join('img', 'icon.png')))
        self.resize(1000, 200)

        self.hex_value=hex_value
        self.ui_panels=['standard']
        for typefile in os.listdir('user'):
            m = re.match(r'(\w+)\.xls', typefile)
            if m is not None:
                self.ui_panels.append(m.group(1))

        main_qw = QWidget()
        hbox_lo = QHBoxLayout()
        ui_fm   = UI_FORM(CFG, self.ui_panels, panel, self.hex_value)
        scroll  = QScrollArea()

        self.setCentralWidget(main_qw)
        hbox_lo.setContentsMargins(0, 0, 0, 0)
        main_qw.setLayout(hbox_lo)
        scroll.setWidget(ui_fm)
        hbox_lo.addWidget(scroll)

        ui_fm.ui_signal_newpanel.connect(self.gen_ui)
        ui_fm.ui_signal_cfg.connect(self.change_cfg)
        self.ui = []

    def gen_ui(self, panel, hex_value):
        self.ui.append(MAIN_UI(panel, hex_value))
        self.ui[-1].show()

    def change_cfg(self, key, value):
        CFG[key] = value
        with open("config.json", 'w') as cfg_file: json.dump(CFG, cfg_file)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MAIN_UI()
    mainWindow.show()
    app.exec_()
    sys.exit()
