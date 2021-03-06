import logging
from common import *
import pygame
from config import *
from pygame.locals import *
from constants import *
from library import *

# class MFD
class MFD:
    scale = 1
    font_file = None
    font = None
    font_bold_file = None
    font_bold = None
    state_file = "mfd.json"
    title = "Elite:Dangerous MFD"
    has_update = False
    show_stkbtn = True
    temp_hide_stkbtn = False

    APP_SIZE = DISPLAY_WIDTH, DISPLAY_HEIGHT
    MFD_MODE = { 1:'NORMAL', 2:'COMBAT', 3:'EXPLORE', 4:'MINING' }
    mode = 0
    LP_STATUS = [ None, 0, 0, 0, 0, 0 ]

    bmp = None
    rpn = None
    upn = None
    mpn = [0, None, None, None, None]
    lpn = None

    @staticmethod
    def set_scale(_scale):
        MFD.scale = _scale
        if MFD.scale != 1:
            MFD.APP_SIZE = int(DISPLAY_WIDTH * MFD.scale), int(DISPLAY_HEIGHT * MFD.scale)

    def set_font(_file, _bold_file):
        MFD.font_file = _file
        MFD.font_bold_file = _bold_file

    def sd(dim):
        return int(dim * MFD.scale)

    def set_update():
        MFD.has_update = True

    def clear_update():
        MFD.has_update = False

    def next_mode():
        MFD.mode += 1
        if MFD.mode > len(MFD.MFD_MODE): MFD.mode = 1
        return MFD.mode

    def prev_mode():
        MFD.mode -= 1
        if MFD.mode < 1: MFD.mode = len(MFD.MFD_MODE)
        return MFD.mode

    def temp_hide_stick_buttons(_on_off):
        MFD.temp_hide_stkbtn = _on_off

    def toggle_show_stick_buttons():
        MFD.show_stkbtn = not MFD.show_stkbtn

    def set_show_stick_buttons(_on_off):
        MFD.show_stkbtn = _on_off

    def set_lp_status(_id, _on_off):
        MFD.LP_STATUS[_id] = _on_off

    def get_lp_status(_id):
        return MFD.LP_STATUS[_id]


# class Image
class Image:

    def __init__(self, _scale):
        # loaded images
        self.BUTTON = pygame.image.load(IMAGE_BUTTON).convert_alpha()
        self.MODE = pygame.image.load(IMAGE_MODE).convert_alpha()
        self.MODEDARK = pygame.image.load(IMAGE_MODE_DARK).convert_alpha()
        self.FSS = pygame.image.load(IMAGE_FSS).convert_alpha()
        self.STKBTN = pygame.image.load(IMAGE_STICK_BUTTON).convert_alpha()
        # created images
        self.BLUR = pygame.Surface(MFD.APP_SIZE)
        self.BLUR.fill(COLOR_GREY)
        self.BLUR.set_alpha(20, RLEACCEL)

        if _scale != 1:
            self.BUTTON = pygame.transform.smoothscale(self.BUTTON, MFD.APP_SIZE)
            self.MODE = pygame.transform.smoothscale(self.MODE, MFD.APP_SIZE)
            self.MODEDARK = pygame.transform.smoothscale(self.MODEDARK, MFD.APP_SIZE)
            _mp_size = MFD.sd(MFD_MP_WIDTH), MFD.sd(MFD_MP_HEIGHT)
            self.FSS = pygame.transform.smoothscale(self.FSS, _mp_size)
            self.STKBTN = pygame.transform.smoothscale(self.STKBTN, _mp_size)


# class MFD_Font
class MFD_Font:

    def __init__(self, _file, _size):
        self.font_file = _file
        self.font_size = _size
        self.font = pygame.font.Font(self.font_file, self.font_size)


# class Button
class Button:
    TYPE_PUSH   = 1
    TYPE_TOGGLE = 2
    TYPE_HOLD   = 3
    TYPE_SWITCH_1 = 11
    TYPE_SWITCH_2 = 21
    STATE_RELEASED = STATE_OFF = 0
    STATE_PUSHED   = STATE_ON  = STATE_HOLD = 1
    TIMER_STEP   = 5  # milliseconds
    TIMER_PUSH   = TIMER_STEP * 2
    TIMER_HOLD   = TIMER_STEP * 20
    TIMER_TOGGLE = -1
    TIMER_SWITCH_1 = -1

    def __init__(self, _name, _joyidx, _pos_x, _pos_y, _color, _type=TYPE_PUSH, _state=STATE_OFF):
        self.name   = _name
        self.joyidx = _joyidx
        if _type <= self.TYPE_SWITCH_1:		# TYPE_PUSH, TYPE_TOGGLE, TYPE_HOLD, TYPE_SWITCH_1
            self.width  = MFD.sd(BTN1_WIDTH)
            self.height = MFD.sd(BTN1_HEIGHT)
        elif _type <= self.TYPE_SWITCH_2:	# TYPE_SWITCH_2
            self.width  = MFD.sd(BTN2_WIDTH)
            self.height = MFD.sd(BTN2_HEIGHT)
        self.pos_x  = MFD.sd(_pos_x)
        self.pos_y  = MFD.sd(_pos_y)
        self.style  = pygame.Surface((self.width, self.height))
        self.style.fill(_color)
        self.style.set_alpha(90, RLEACCEL)
        self.type   = _type
        self.state  = _state
        self.timer  = 0

    def get_offset(self):
        return (self.pos_x, self.pos_y)

    def get_rect(self):
        return (self.pos_x, self.pos_y, self.width, self.height)

    def get_size(self):
        return (self.width, self.height)

    def default_timer(self):
        if self.type == self.TYPE_PUSH:     self.timer = self.TIMER_PUSH
        if self.type == self.TYPE_TOGGLE:   self.timer = self.TIMER_TOGGLE
        if self.type == self.TYPE_HOLD:     self.timer = self.TIMER_HOLD
        if self.type == self.TYPE_SWITCH_1: self.timer = self.TIMER_SWITCH_1

    def set_state(self, state):
        self.state = state
        self.default_timer()

    def update_state(self):
        if self.type == self.TYPE_PUSH:
            self.state = self.STATE_PUSHED
        if self.type == self.TYPE_TOGGLE:
            self.state = (self.state + 1) % 2
        if self.type == self.TYPE_HOLD:
            self.state = self.STATE_ON
        if self.type == self.TYPE_SWITCH_1:
            self.state = (self.state + 1) % 2
        self.default_timer()

    def reset_state(self):
        self.state = self.STATE_OFF
        self.timer = 0

    def activated(self):
        if self.state == self.STATE_ON: return True
        else: return False

    def tick(self):
        if self.timer > 0:
            self.timer -= 1
            return False
        else:
            self.state = self.STATE_OFF
            return True


# class Coriolis
class Coriolis:

    def __init__(self, p_width):
        self.layout = pygame.image.load(IMAGE_CORIOLIS_LAYOUT)
        self.padnum = pygame.image.load(IMAGE_CORIOLIS_PADNUM)
        self.width  = self.layout.get_width()
        self.height = self.layout.get_height()
        self.scale  = 1

        s_width = MFD.sd(p_width)
        orig_width = self.width
        if orig_width > s_width:
            s_height = int(s_width * self.height / self.width)
            self.layout = pygame.transform.smoothscale(self.layout, (s_width, s_height))
            self.padnum = pygame.transform.smoothscale(self.padnum, (s_width, s_height))
            self.width = s_width
            self.height = s_height
            self.scale = s_width / orig_width

# class Panel
class Panel:

    def __init__(self, pos_x, pos_y, width, height, rows, font_size=None, bold=False, mode=None):
        self.pos_x  = pos_x
        self.pos_y  = pos_y
        self.width  = width
        self.height = height
        self.rows   = rows
        self.f_size = MFD.sd(FONT_SIZE)
        if font_size: self.f_size = font_size
        self.lines  = [ ( "", "", COLOR_BLACK ) ] * self.rows
        self.pyfont  = MFD_Font(MFD.font_file, self.f_size)
        self.pyfontb = MFD_Font(MFD.font_bold_file, self.f_size)
        self.is_bold = bold
        self.mfd_mode = mode

    def get_offset(self):
        return (self.pos_x, self.pos_y)

    def get_size(self):
        return (self.width, self.height)

    def clear_all(self):
        self.lines  = [ ( "", "", COLOR_BLACK ) ] * self.rows
        MFD.set_update()

    def add_text(self, text_lines, color=None):
        if not color: color = COLOR_ORANGE	# default panel text color
        for text in text_lines:
            if self.is_bold:
                wrapped_text = wrap_text(text, self.pyfontb.font, self.width)
            else:
                wrapped_text = wrap_text(text, self.pyfont.font, self.width)
            for t in reversed(wrapped_text):
                self.add_lines( [ ("text", t, color) ] )
                MFD.set_update()

    def add_lines(self, lines):
        if len(lines) > self.rows: lines = lines[:self.rows]
        self.lines = lines + self.lines[:(self.rows - len(lines))]
        MFD.set_update()

    def shift_lines(self, num_lines, _type):
        if num_lines > self.rows: num_lines = self.rows
        self.lines = [ ( _type, "", COLOR_BLACK ) ] * num_lines + self.lines[:(self.rows - num_lines)]
        MFD.set_update()

    def add_image(self, imagefile, attr=None):
        try:
            img = pygame.image.load(imagefile)
            s_height = img.get_height()
            s_width = self.width - 16
            if img.get_width() > s_width:
                s_height = int(s_width * img.get_height() / img.get_width())
                img = pygame.transform.smoothscale(img, (s_width, s_height))
            num_rows = int((s_height + self.f_size - 1) / self.f_size)
            self.shift_lines(num_rows, "empty")
            self.lines = [ ( "image", img, attr ) ] + self.lines[:(self.rows - 1)]
            MFD.set_update()
        except Exception as e:
            logger.error("Error: %s" % e)

    def add_coriolis(self, pad, _coriolis):
        num_rows = int((_coriolis.height + self.f_size - 1) / self.f_size)
        self.shift_lines(num_rows, "empty")
        self.lines = [ ( "coriolis", pad, _coriolis ) ] + self.lines[:(self.rows - 1)]
        MFD.set_update()

    def render_panel(self, surface):
        for row, (_type, _content, _extra_attr) in enumerate(self.lines):
            if _type == "text":
                # _content = text
                # _extra_attr = color
                if self.is_bold:
                    label = self.pyfontb.font.render(_content, True, _extra_attr)
                else:
                    label = self.pyfont.font.render(_content, True, _extra_attr)
                surface.blit(label, (self.pos_x + 3, self.pos_y + row * self.f_size))
            if _type == "image":
                # _content = pygame surface
                # _extra_attr = offset: (x_offset, y_offset)
                if _extra_attr:
                    x_offset = _extra_attr[0]
                    _extra_height = _extra_attr[1] * 2
                else:
                    x_offset = int((self.width - _content.get_width()) / 2)
                    _extra_height = 0
                _img_height = _content.get_height()
                num_rows = int((_img_height + _extra_height + self.f_size - 1) / self.f_size)
                y_offset = int((num_rows * self.f_size - _img_height) / 2)
                surface.blit(_content, (self.pos_x + x_offset, self.pos_y + row * self.f_size + y_offset))
            if _type == "coriolis":
                # _content = pad number
                # _extra_attr = coriolis instance
                coriolis = _extra_attr
                x_offset = int((self.width - coriolis.width) / 2)
                num_rows = int((coriolis.height + self.f_size - 1) / self.f_size)
                y_offset = int((num_rows * self.f_size - coriolis.height) / 2)
                position = self.pos_x + x_offset, self.pos_y + row * self.f_size + y_offset
                display_rows = self.rows - row + 1
                display_area = (0, 0, coriolis.width - 1, display_rows * self.f_size - 1)
                surface.blit(coriolis.layout, position, display_area)
                if _content == 0:
                    surface.blit(coriolis.padnum, position, display_area)
                if _content > 0:
                    num_pos = CORIOLIS_POS[_content - 1]
                    x = int(num_pos[0] * coriolis.scale)
                    y = int(num_pos[1] * coriolis.scale)
                    w = int((num_pos[2] - num_pos[0]) * coriolis.scale)
                    h = int((num_pos[3] - num_pos[1]) * coriolis.scale)
                    if y > self.height: y = self.height
                    if h > self.height: h = self.height
                    surface.blit(coriolis.padnum, (position[0] + x, position[1] + y), (x, y, w, h))

# class MFD_Mode_Status
class MFD_Mode_Status:

    def __init__(self):
        self.ind_xy = []
        self.ind_area = []
        for m in range(0, len(MFD.MFD_MODE)):
            m_pos = MFD_MODE_POS[m + 1]
            x = MFD.sd(m_pos[0])
            y = MFD.sd(m_pos[1])
            w = MFD.sd(m_pos[2] - m_pos[0])
            h = MFD.sd(m_pos[3] - m_pos[1])
            self.ind_xy.append( (x, y) )
            self.ind_area.append( (x, y, w, h) )

        self.sts_xy = []
        self.sts_area = []
        for s in range(0, len(MFD.LP_STATUS)):
            s_pos = STS_POS[s]
            x = MFD.sd(s_pos[0])
            y = MFD.sd(s_pos[1])
            w = MFD.sd(s_pos[2] - s_pos[0])
            h = MFD.sd(s_pos[3] - s_pos[1])
            self.sts_xy.append( (x, y) )
            self.sts_area.append( (x, y, w, h) )
