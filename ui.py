# encoding=utf-8
import os, re, sys, webbrowser, xlrd
from PyQt5.QtCore import pyqtSignal, QFileInfo, Qt
from PyQt5.QtGui import QIntValidator, QCursor
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QWidget, QComboBox, \
    QPushButton, QRadioButton, QLabel, QFrame, QGridLayout, QMenu, QColorDialog
from main import LG  as LG


#####################################################################
class BitQLE(QLineEdit):
    def mouseDoubleClickEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def mousePressEvent(self, event):
        if self.text() == "0":
            self.setText("1")
        else:
            self.setText("0")
        self.clearFocus()
        self.deselect()


class data_struct(object):
    def __init__(self, panel='standard', hex_value=''):
        self.mode = 16
        self._panel = panel
        self._bits = 64
        self.value_sub = ['' for i in range(2)]
        self.update(hex_value)

    def standard(self):
        return self._panel == 'standard'

    def bits(self):
        return self._bits

    def panel(self):
        return self._panel

    def setBits(self, bits):
        self._bits = bits
        sub_num = self._bits // 32
        if self._bits % 32 != 0: sub_num += 1
        self.value_sub = ['' for i in range(sub_num)]
        self.update(self.hex_value, 16)

    def setPanel(self, panel):
        self._panel = panel

    def sub_value_wide(self):
        if self.mode == 16:
            return 8
        elif self.mode == 10:
            return 10
        elif self.mode == 8:
            return 11

    def full_value_wide(self):
        if self.mode == 16:
            return len(str(hex(int('1' * self._bits, base=2)))) - 2
        elif self.mode == 10:
            return len(str(int('1' * self._bits, base=2)))
        elif self.mode == 8:
            return len(str(oct(int('1' * self._bits, base=2)))) - 2

    def update(self, value, mode=None):
        if mode is None: mode = self.mode
        self.hex_value = self.value_translate(value, mode, 16)
        self.dec_value = self.value_translate(value, mode, 10)
        self.oct_value = self.value_translate(value, mode, 8)
        self.bin_value = self.value_translate(value, mode, 2)
        self.value_str = self.hex_value if self.mode == 16 else self.dec_value
        self.value_str = self.oct_value if self.mode == 8 else self.value_str
        self.value_str = '' if self.value_str == '0' else self.value_str

        full_hex_value = '0' * (self._bits // 4 + 1) + self.hex_value
        for i in range(len(self.value_sub)):
            self.value_sub[i] = self.value_translate(full_hex_value[-8:], 16,
                                                     self.mode)
            if self.value_sub[i] == '0': self.value_sub[i] = ''
            full_hex_value = full_hex_value[:-8]

    def update_bysub(self, sub_txt, i, mode=None):
        if mode is None: mode = self.mode
        org_fvalue_hex = '0' * (self._bits // 4 + 1) + self.hex_value
        sub_hex = '0' * 8 + self.value_translate(sub_txt, mode, 16)
        new_hex = org_fvalue_hex[:-8 * (i + 1)] + sub_hex[-8:]
        if i > 0: new_hex = new_hex + org_fvalue_hex[-8 * i:]
        self.update(new_hex, 16)

    def value_translate(self, value_txt, pre_mode, post_mode):
        if value_txt == '':
            return '0'
        elif post_mode == 16:
            return str(hex(int(value_txt, pre_mode)))[2:].upper()
        elif post_mode == 10:
            return str(int(value_txt, pre_mode))
        elif post_mode == 8:
            return str(oct(int(value_txt, pre_mode)))[2:]
        elif post_mode == 2:
            return str(bin(int(value_txt, pre_mode)))[2:]
        else:
            return value_txt

    def value_proc(self, txt):
        m = None
        if self.mode == 16:
            m = re.match(r'.*[^\da-fA-F]|^0', txt)
            txt = re.sub(r'[^\da-fA-F]', '', txt)
        elif self.mode == 10:
            m = re.match(r'.*[^0-9]|^0', txt)
            txt = re.sub(r'[^0-9]', '', txt)
        elif self.mode == 8:
            m = re.match(r'.*[^0-7]|^0', txt)
            txt = re.sub(r'[^0-7]', '', txt)
        txt = re.sub(r'^0*', '', txt)
        if m is None:
            return txt, 0
        else:
            return txt, 1


class user_define:
    def __init__(self, file_name):
        self.file_name = file_name

    def gen_info(self, sheet_name="default"):
        self.bits = 0
        self.sheet_spec = ""
        self.name = []
        self.end = []
        self.start = []
        self.spec = []
        self.vspec = []

        file = xlrd.open_workbook(self.file_name)
        self.form_lst = file.sheet_names()
        if sheet_name == "default": sheet_name = self.form_lst[0]

        sh = file.sheet_by_name(sheet_name)
        if sh.nrows != 0:
            total_cols_n = sh.row_values(0).index("total")
            end_cols_n = sh.row_values(0).index("end")
            start_cols_n = sh.row_values(0).index("start")
            name_cols_n = sh.row_values(0).index("name")
            spec_cols_n = sh.row_values(0).index("spec")
            vspec_cols_n = sh.row_values(0).index("value_spec")

        msg = None
        if sh.nrows == 0 or total_cols_n is None or name_cols_n is None or \
                start_cols_n is None or end_cols_n is None or \
                spec_cols_n is None or vspec_cols_n is None:
            msg = "%s.%s: first line not[total/end/start/name/spec/value_spec]! Quit!" % (
            self.file_name, sheet_name)
        elif sh.nrows < 2 or sh.cell_value(1, total_cols_n) == "":
            msg = "%s.%s: A2 cell total bit nums is not set! Quit!" % (
            self.file_name, sheet_name)
        if msg is not None:
            QMessageBox.about(self.parent, 'error', msg)
            sys.exit(0)

        self.bits = int(sh.cell_value(1, total_cols_n))
        self.sheet_spec = sh.cell_value(2, total_cols_n)

        for i, name in enumerate(sh.col_values(name_cols_n)):
            if i == 0: continue
            self.name.append(name)
            self.spec.append(sh.cell_value(i, spec_cols_n))
            s = sh.cell_value(i, start_cols_n)
            e = sh.cell_value(i, end_cols_n)
            if (s != "" and e != "" and int(s) > int(e)) or (
                    s == "" and e == ""):
                QMessageBox.about(self.parent, 'error',
                                  "%s.%s line %d: must end >= start! Quit!" % (
                                  self.file_name, sheet_name))
                sys.exit(0)
            elif s == "":
                s = e
            elif e == "":
                e = s

            self.start.append(int(s))
            self.end.append(int(e))

            info, value = self.value_spec_proc(sh.cell_value(i, vspec_cols_n))
            if info == "none" or info == "valid":
                self.vspec.append(value)
            else:
                msg = 'error', "%s.%s line %d: value_spec must is 0xXX=>format or none! Quit!" % (
                self.file_name, sheet_name, i + 1)
                QMessageBox.about(self.parent, msg)
                sys.exit(0)

        if len(self.end) > 0 and self.end[-1] != '' and self.bits <= self.end[
            -1]:
            msg = 'error', "%s.%s line %d: A2 cell total bit nums must>end! Quit!" % (
            self.file_name, sheet_name, i + 1)
            QMessageBox.about(self.parent, msg)
            sys.exit(0)

    def value_spec_proc(self, value_spec):
        dic_value = {}
        if value_spec == "":
            return 'none', dic_value
        else:
            for line in value_spec.splitlines():
                if line == "": continue
                m = re.match(r'0x([\da-fA-F]+)=>(.*)', line)
                if m is not None:
                    key, value = int(m.group(1), 16), m.group(2)
                    dic_value[key] = value
                else:
                    return 'invalid', ''
            return 'valid', dic_value


class UI_FORM(QWidget):
    ui_signal_newpanel = pyqtSignal(str, str)
    ui_signal_cfg = pyqtSignal(str, str)

    def __init__(self, cfg, ui_panels, panel='standard', bit_value=''):
        super(UI_FORM, self).__init__()
        self.CFG = cfg
        self.lg = 0 if self.CFG["language"] == "English" else 1
        self.ui_panels = ui_panels
        self.DS = data_struct(panel, bit_value)

        self.panel_proc()
        self.ui_x, self.ui_y = 990, 150
        self.setupUi()

    def panel_proc(self, sheet_name='default'):
        if self.DS.standard():
            self.form_item = ['64bits', '32bits', '128bits', '256bits',
                              '512bits']
            if sheet_name != 'default':
                self.DS.setBits(int(sheet_name))
        else:
            if sheet_name == 'default':
                filepath = os.path.join('user', self.DS.panel() + '.xls')
                self.user_def = user_define(filepath)

            self.user_def.gen_info(sheet_name)
            self.form_item = self.user_def.form_lst
            self.DS.setBits(self.user_def.bits)

    def setupUi(self):
        cb_forms = QComboBox(self)
        cb_forms.addItems(self.form_item)
        p = 0 if self.DS.standard() else 80
        cb_forms.resize(80 + p, 28)
        cb_forms.move(20, 9)
        cb_forms.activated[str].connect(self.evt_form_select)

        btn_color = QPushButton(LG['color'][self.lg], self)
        btn_color.move(110 + p, 8)
        btn_color.resize(50, 30)
        btn_color.clicked.connect(self.evt_color_btn)

        rb_mod_hex = QRadioButton('16', self)
        rb_mod_dec = QRadioButton('10', self)
        rb_mod_oct = QRadioButton('8', self)
        rb_mod_hex.move(250, 15)
        rb_mod_dec.move(290, 15)
        rb_mod_oct.move(330, 15)
        rb_mod_hex.setChecked(True)
        rb_mod_hex.toggled.connect(lambda: self.evt_radio_btn(rb_mod_hex))
        rb_mod_dec.toggled.connect(lambda: self.evt_radio_btn(rb_mod_dec))
        rb_mod_oct.toggled.connect(lambda: self.evt_radio_btn(rb_mod_oct))

        btn_lshift = QPushButton('<<', self)
        btn_lshift.move(380, 8)
        btn_lshift.resize(20, 30)
        btn_lshift.clicked.connect(
            lambda: self.evt_shift_btn(LG['left'][self.lg]))

        self.tx_shift = QLineEdit(self)
        self.tx_shift.setText('1')
        intValidator = QIntValidator()
        intValidator.setRange(1, 99)
        self.tx_shift.setValidator(intValidator)
        self.tx_shift.setStyleSheet('background-color: #f0f0f0')
        self.tx_shift.setAlignment(Qt.AlignCenter)
        self.tx_shift.setContextMenuPolicy(Qt.NoContextMenu)
        self.tx_shift.resize(20, 28)
        self.tx_shift.move(400, 9)

        btn_rshift = QPushButton('>>', self)
        btn_rshift.move(420, 8)
        btn_rshift.resize(20, 30)
        btn_rshift.clicked.connect(
            lambda: self.evt_shift_btn(LG['right'][self.lg]))

        lb_msb = QLabel(LG["MSB"][self.lg], self)
        lb_msb.move(455, 18)

        self.UI_value_top()
        self.UI_value_bit()
        self.UI_value_sub()
        if not self.DS.standard(): self.UI_field()
        self.UI_right_menu()
        self.uiflush_all()

    def UI_value_top(self):
        self.bit_wight = 7
        self.tx_topvalue = QLineEdit(self)
        input_length = self.DS.full_value_wide()
        self.tx_topvalue.setMaxLength(input_length)
        self.tx_topvalue.move(480, 8)
        self.tx_topvalue.resize(self.bit_wight * input_length, 30)
        self.tx_topvalue.setAlignment(Qt.AlignRight)
        self.tx_topvalue.setFocus()
        self.tx_topvalue.textChanged.connect(self.evt_value_top)

        if input_length > 50: self.ui_x = 500 + self.bit_wight * input_length
        self.setMinimumSize(self.ui_x, self.ui_y)

    def UI_value_bit(self):
        self.fm1 = QFrame(self)
        p = 0 if self.DS.bits() % 32 == 0 else 1
        self.fm1.resize(800, 20 + (self.DS.bits() // 32 + p) * 45)
        self.ui_y = 50 + 20 + (self.DS.bits() // 32 + p) * 45
        self.fm1.move(20, 42)
        self.fm1.setFrameShape(QFrame.Box)
        self.fm1grid = QGridLayout()
        self.fm1.setLayout(self.fm1grid)
        self.setMinimumSize(self.ui_x, self.ui_y)

        self.tx_bit = []
        bin_len = len(self.DS.bin_value)
        for i in range(self.DS.bits()):
            lb_bit = QLabel(str(i), self.fm1)
            lb_bit.setAlignment(Qt.AlignCenter)
            redcolor = ';color:red' if i % 8 == 0 else ''
            fontsize = 'font-size:7pt' if i > 99 else 'font-size:8pt'
            lb_bit.setStyleSheet(fontsize + redcolor)

            self.fm1grid.addWidget(lb_bit, *(i // 32 * 2, 31 - i % 32))
            self.tx_bit.append(BitQLE(self.fm1))
            self.tx_bit[i].setMaxLength(1)
            self.tx_bit[i].setReadOnly(0)
            self.tx_bit[i].setAlignment(Qt.AlignCenter)
            self.tx_bit[i].setContextMenuPolicy(Qt.NoContextMenu)

            self.fm1grid.addWidget(self.tx_bit[i],
                                   *(i // 32 * 2 + 1, 31 - i % 32))
            self.tx_bit[i].textChanged.connect(self.evt_value_bit)

    def UI_value_sub(self):
        input_length = self.DS.sub_value_wide()
        self.fm2 = QFrame(self)
        p = 0 if self.DS.bits() % 32 == 0 else 1
        self.fm2.resize(10 + 10 * input_length,
                        20 + (self.DS.bits() // 32 + p) * 45)
        self.fm2.move(830, 42)
        self.fm2.setFrameShape(QFrame.Box)
        self.fm2grid = QGridLayout()
        self.fm2.setLayout(self.fm2grid)

        self.value_sub = []
        for i in range(len(self.DS.value_sub)):
            value_sub_lb = QLabel(LG['sub'][self.lg] + str(i), self.fm2)
            self.value_sub.append(QLineEdit(self.fm2))
            self.value_sub[-1].setMaxLength(input_length)
            self.value_sub[-1].setAlignment(Qt.AlignRight)
            self.value_sub[-1].textChanged.connect(self.evt_value_sub)

            self.fm2grid.addWidget(value_sub_lb, *(i * 2, 0))
            self.fm2grid.addWidget(self.value_sub[-1], *(i * 2 + 1, 0))

    def UI_right_menu(self):
        self.right_menu = QMenu(self)
        self.rm_clear = self.right_menu.addAction(LG['clear'][self.lg])
        self.rm_reverse = self.right_menu.addAction('~')
        self.rm_ones = self.right_menu.addAction(LG["ones"][self.lg])
        self.rm_newpanel = self.right_menu.addMenu(LG['newpanel'][self.lg])
        for panel in self.ui_panels:
            new_pannel = self.rm_newpanel.addAction(panel)
            new_pannel.triggered.connect(
                lambda: self.evt_right_menu('newpanel', self.sender().text()))

        self.rm_help = self.right_menu.addMenu(LG['help'][self.lg])
        self.rm_about = self.rm_help.addAction(LG["about"][self.lg])
        self.rm_guide = self.rm_help.addAction(LG["guide"][self.lg])

        self.rm_lang = self.right_menu.addMenu(LG["language"][self.lg])
        self.rm_lang_e = self.rm_lang.addAction("English")
        self.rm_lang_c = self.rm_lang.addAction("中文")

        self.rm_clear.triggered.connect(lambda: self.evt_right_menu('clear'))
        self.rm_reverse.triggered.connect(
            lambda: self.evt_right_menu('reverse'))
        self.rm_ones.triggered.connect(lambda: self.evt_right_menu('one_num'))
        self.rm_about.triggered.connect(lambda: self.evt_right_menu('about'))
        self.rm_guide.triggered.connect(lambda: self.evt_right_menu('guide'))
        self.rm_lang_e.triggered.connect(lambda: self.evt_right_menu('lang_e'))
        self.rm_lang_c.triggered.connect(lambda: self.evt_right_menu('lang_c'))

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_right_menu)

    def UI_field(self):
        self.fm3 = QFrame(self)
        length = len(self.user_def.name)
        self.fm3.resize(800, 20 + (length + 1) * 25)
        self.fm3.move(20, self.ui_y)
        self.ui_y = self.ui_y + 20 + (length + 1) * 25 + 20

        self.fm3.setFrameShape(QFrame.Box)
        self.fm3grid = QGridLayout()
        self.fm3.setLayout(self.fm3grid)
        self.setMinimumSize(self.ui_x, self.ui_y)

        lb_field = QLabel('field', self.fm3)
        lb_name = QLabel('name', self.fm3)
        lb_value = QLabel('value', self.fm3)
        lb_value_spec = QLabel('value_spec', self.fm3)
        self.fm3grid.addWidget(lb_field, *(0, 0), 1, 1)
        self.fm3grid.addWidget(lb_name, *(0, 1), 1, 1)
        self.fm3grid.addWidget(lb_value, *(0, 2), 1, 1)
        self.fm3grid.addWidget(lb_value_spec, *(0, 3), 1, 1)

        self.lb_field_v = []
        self.lb_field_vs = []
        for i in range(length):
            if self.user_def.end[i] != '':
                rang_str = ':' + str(self.user_def.start[i]) \
                    if self.user_def.end[i] != self.user_def.start[i] else ''
                lb_field_f = QLabel(
                    '[' + str(self.user_def.end[i]) + rang_str + ']', self.fm3)

                lb_field_n = QLabel(self.user_def.name[i], self.fm3)
                lb_field_n.setToolTip(self.user_def.spec[i])
                self.lb_field_v.append(QLabel('0', self.fm3))
                self.lb_field_vs.append(QLabel('', self.fm3))

                self.fm3grid.addWidget(lb_field_f, *(i + 1, 0))
                self.fm3grid.addWidget(lb_field_n, *(i + 1, 1))
                self.fm3grid.addWidget(self.lb_field_v[-1], *(i + 1, 2))
                self.fm3grid.addWidget(self.lb_field_vs[-1], *(i + 1, 3))

        lb_sheet_spec = QLabel(self.user_def.sheet_spec, self.fm3)
        lb_sheet_spec.setStyleSheet('font-style:italic;color:#55AA00')
        self.fm3grid.addWidget(lb_sheet_spec, length + 1, 0, 1, 4,
                               Qt.AlignCenter)

    # ---------------------------------------------------------
    def show_right_menu(self):
        self.right_menu.exec_(QCursor.pos())

    def evt_right_menu(self, cmd, panelname=''):
        if cmd == 'clear':
            self.DS.update('')
            self.uiflush_all()
        elif cmd == 'reverse':
            bin_value = self.DS.bin_value
            len_bin_value = len(bin_value)
            new_value = ''
            for i in range(self.DS.bits()):
                if i < len_bin_value:
                    if bin_value[i] == '0':
                        new_value = new_value + '1'
                    else:
                        new_value = new_value + '0'
                else:
                    new_value = '1' + new_value
            self.DS.update(new_value, 2)
            self.uiflush_all()
        elif cmd == 'one_num':
            bin_value = self.DS.bin_value
            one_num = 0
            for i in bin_value:
                if i == '1': one_num += 1
            QMessageBox.about(self, '1 nums', 'all 1 nums:\n' + str(one_num))
        elif cmd == 'about':
            if self.CFG['language'] == "English":
                about_str = "Author : Yukun.Gong\nVersion: %s\nCreate : 2022-5-1" % (
                self.CFG['version'])
            else:
                about_str = "作者: 巩玉坤\n版本: %s\n创建: 2022-5-1" % (
                self.CFG["version"])
            QMessageBox.about(self, LG['about'][self.lg], about_str)
        elif cmd == 'guide':
            webbrowser.open('https://gitcode.net/weixin_37548620/bitanalyzer/-/tree/master/readme.md')
        elif cmd == 'newpanel':
            self.ui_signal_newpanel.emit(panelname, self.DS.hex_value)
        elif cmd == 'lang_e' or cmd == 'lang_c':
            self.CFG["language"] = "English" if cmd == 'lang_e' else "中文"
            self.ui_signal_cfg.emit('language', self.CFG["language"])
            self.ui_signal_newpanel.emit(self.ui_panels[0], self.DS.hex_value)

    def evt_shift_btn(self, cmd):
        value = int(self.DS.dec_value)
        if cmd == 'left':
            value <<= int(self.tx_shift.text())
        elif cmd == 'right':
            value >>= int(self.tx_shift.text())
        bin_str = str(bin(value))[2:]
        bin_len = len(bin_str)
        if bin_len > self.DS.bits(): bin_str = bin_str[
                                               bin_len - self.DS.bits():]

        self.DS.update(bin_str, 2)
        self.uiflush_all()

    def evt_form_select(self, text):
        self.panel_proc(text[:-4]) if self.DS.standard() else self.panel_proc(
            text)

        self.tx_topvalue.deleteLater()
        self.fm1.deleteLater()
        self.fm1grid.deleteLater()
        self.fm2.deleteLater()
        self.fm2grid.deleteLater()
        for i in self.tx_bit:    i.deleteLater()
        for i in self.value_sub: i.deleteLater()
        if not self.DS.standard():
            self.fm3.deleteLater()
            self.fm3grid.deleteLater()
            for i in self.lb_field_v: i.deleteLater()
            for i in self.lb_field_vs: i.deleteLater()

        self.UI_value_top()
        self.UI_value_bit()
        self.UI_value_sub()
        if not self.DS.standard(): self.UI_field()

        self.tx_topvalue.show()
        self.fm1.show()
        self.fm2.show()
        if not self.DS.standard(): self.fm3.show()

        self.setMinimumSize(self.ui_x, self.ui_y)

        self.DS.update(self.DS.hex_value, 16)
        self.uiflush_all()

    def evt_color_btn(self):
        self.CFG['bcolor'] = QColorDialog.getColor().name()
        self.ui_signal_cfg.emit('bcolor', self.CFG['bcolor'])
        self.uiflush_value_bit()

    def evt_radio_btn(self, btn):
        if btn.isChecked():
            if btn.text() == '16':
                self.DS.mode = 16
            elif btn.text() == '10':
                self.DS.mode = 10
            elif btn.text() == '8':
                self.DS.mode = 8
            self.DS.update(self.DS.hex_value, 16)

            self.tx_topvalue.deleteLater()
            for i in self.value_sub: i.deleteLater()
            self.fm2.deleteLater()
            self.fm2grid.deleteLater()

            self.UI_value_top()
            self.UI_value_sub()

            self.tx_topvalue.show()
            self.fm2.show()
            self.setMinimumSize(self.ui_x, self.ui_y)
            self.uiflush_all()

    def evt_value_top(self):
        cursor_p = self.tx_topvalue.cursorPosition()
        top_value = self.tx_topvalue.text()
        top_value, fault_input_flag = self.DS.value_proc(top_value)

        self.DS.update(top_value)
        self.uiflush_all()
        self.tx_topvalue.setCursorPosition(cursor_p - fault_input_flag)

    def evt_value_bit(self, i):
        topvalue = ''
        for i in self.tx_bit: topvalue = i.text() + topvalue
        self.DS.update(topvalue, 2)
        self.uiflush_all()

    def evt_value_sub(self):
        for p, sub_i in enumerate(self.value_sub):
            if sub_i.isModified():
                sub_i.setModified(False)
                cursor_p = sub_i.cursorPosition()
                sub_txt = sub_i.text()
                sub_txt, fault_input_flag = self.DS.value_proc(sub_txt)

                self.DS.update_bysub(sub_txt, p)
                self.uiflush_all()
                sub_i.setCursorPosition(cursor_p - fault_input_flag)
                break

    # ----------------------------------------
    def uiflush_all(self):
        self.tx_topvalue.textChanged.disconnect(self.evt_value_top)
        self.tx_topvalue.setText(self.DS.value_str)
        self.tx_topvalue.textChanged.connect(self.evt_value_top)

        for p in range(len(self.DS.value_sub)):
            self.value_sub[p].textChanged.disconnect(self.evt_value_sub)
            self.value_sub[p].setText(self.DS.value_sub[p])
            self.value_sub[p].textChanged.connect(self.evt_value_sub)

        self.uiflush_value_bit()
        if not self.DS.standard(): self.uiflush_value_field()

    def uiflush_value_bit(self):
        bin_value = self.DS.bin_value
        length = len(bin_value)
        for i in range(self.DS.bits()):
            self.tx_bit[i].textChanged.disconnect(self.evt_value_bit)
            bit_str = bin_value[length - 1 - i] if i < length else '0'
            bit_color = "#ffffff" if bit_str == '0' else self.CFG['bcolor']
            self.tx_bit[i].setText(bit_str)
            self.tx_bit[i].setStyleSheet(
                "QWidget {background-color:%s}" % (bit_color))
            self.tx_bit[i].textChanged.connect(self.evt_value_bit)

    def uiflush_value_field(self):
        bin_value = '0' * (
                    self.DS.bits() - len(self.DS.bin_value)) + self.DS.bin_value
        field_num = len(self.user_def.name)
        if len(self.lb_field_v) > 0:
            for i in range(field_num):
                v = ''
                if self.user_def.end[i] != self.user_def.start[i]:
                    v = bin_value[self.DS.bits() - self.user_def.end[
                        i] - 1: self.DS.bits() - self.user_def.start[i]]
                elif self.user_def.end[i] != '':
                    v = bin_value[self.DS.bits() - self.user_def.end[i] - 1]
                vl = int(v, 2)
                self.lb_field_v[i].setText(str(hex(vl)))

                vs = '' if vl not in self.user_def.vspec[i] else \
                self.user_def.vspec[i][vl]
                self.lb_field_vs[i].setText(vs)
