import sys, os
import numpy as np

sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator, SpeedModulator
from common.wavesrc import WaveBuffer, WaveFile
from common.gfxutil import topleft_label, resize_topleft_label, CLabelRect, KFAnim, AnimGroup, CEllipse, CRectangle

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, BindTexture
from kivy.core.window import Window
from kivy.core.image import Image

from numpy import random

from common.kivyparticle import ParticleSystem

# configuration parameters:
ground_h = 0.2  # height of ground from the bottom of screen (as proportion of window height)
ground_w_margin = 0.1  # margin on either side of the ground (as proportion of window width)
time_span = 2.7  # time (in seconds) that spans the full horizontal width of the Window
build_width = 0.10  # horizontal width of building (as a proportion of window width)
build_height = 0.15
build_gap = 0.10
mark_to_gap = 0.0
marker_width = 0.05
marker_height = 0.03

slop_window = 100


def time_to_xpos(time, win_size):
    middle = win_size[0] / 2
    slope = win_size[0] / time_span
    return slope * time + middle


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        track1 = 'data/lead_violin.wav'
        track2 = 'data/drums.wav'
        track3 = 'data/ambience.wav'
        track4 = 'data/bass.wav'

        build_markers = 'data/annotations.txt'

        self.audio_ctrl = AudioController([track1, track2, track3, track4])
        self.song_data = SongData(build_markers)
        self.display = GameDisplay(self.song_data)

        self.canvas.add(self.display)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.audio_ctrl.toggle()

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.audio_ctrl.toggle()

        # button down
        button_idx = lookup(keycode[1], '1234', (0, 1, 2, 3))
        if button_idx != None:
            print('down', button_idx)
            # mute/unmute track
            self.audio_ctrl.mute_track(button_idx)

    # handle changing displayed elements when window size changes
    def on_layout(self, win_size):
        resize_topleft_label(self.info)

    def on_update(self):
        self.audio_ctrl.on_update()
        now = self.audio_ctrl.get_time()
        self.display.on_update(now)

        self.info.text = 'p: pause/unpause music\n'
        self.info.text += 'song time: {:.2f}\n'.format(now)


class SongData(object):
    def __init__(self, filepath):
        super(SongData, self).__init__()
        self.build_path = filepath
        self.builds = []

    def make_clicks(self):
        build_file = open(self.build_path)
        line_list = build_file.readlines()
        for line in line_list:
            tokens = line.strip().split('\t')
            self.builds.append((float(tokens[0]), int(tokens[1])))

    def set_gem_path(self, filepath):
        self.build_path = filepath

    def get_clicks(self):
        return self.builds


class Track(object):
    def __init__(self, path):
        super(Track, self).__init__()
        self.mute = False
        self.gen = WaveGenerator(WaveFile(path))
        if path == 'data/tutorial.wav':
            self.gen.set_gain(0.6)
        self.speed_mod = SpeedModulator(self.gen, 1.0)

    def play_toggle(self):
        self.gen.play_toggle()

    def restart(self):
        self.gen.reset()

    def mute_unmute(self):
        if self.mute:
            self.gen.set_gain(1.0)
        else:
            self.gen.set_gain(0.0)
        self.mute = not self.mute

    def set_gain(self, gain):
        self.gen.set_gain(gain)


class AudioController(object):
    def __init__(self, song_paths):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)
        self.speed_change = False

        # add tracks to mixer
        self.tracks = [Track(path) for path in song_paths]
        for track in self.tracks:
            self.mixer.add(track.speed_mod)
        # miss fx
        fx_path = 'data/miss.wav'
        self.miss_fx = WaveGenerator(WaveFile(fx_path))
        self.miss_fx.set_gain(0.8)

    # start / stop all parts of the song
    def toggle(self):
        for track in self.tracks:
            track.play_toggle()

    def restart_song(self):
        for track in self.tracks:
            track.restart()

    # play miss sound effect
    def play_miss(self):
        self.mixer.add(self.miss_fx)
        self.miss_fx.reset()
        self.miss_fx.play()

    # mute/unmute individual tracks
    def mute_track(self, index):
        self.tracks[index].mute_unmute()

    # function for changing speed of tracks with powerups
    def speed_toggle(self, key):
        if self.speed_change:
            speed = 1.0
        else:
            if key == 'slow':
                speed = 0.9
            elif key == 'fast':
                speed = 1.1
            else:
                speed = 1.0
        for track in self.tracks:
            track.speed_mod.set_speed(speed)
        self.speed_change = not self.speed_change

    # return current time (in seconds) of song
    def get_time(self):
        return self.tracks[0].gen.frame / Audio.sample_rate

    # update audio
    def on_update(self):
        self.audio.on_update()


class MarkerLines(InstructionGroup):
    def __init__(self, marker):
        super(MarkerLines, self).__init__()
        self.time = marker.time
        self.height = marker.height
        self.marker = marker.marker

        self.color = Color(rgb=(1, 1, 1))

        self.width = marker_width * Window.size[0] / 25

        self.top_line = Line(width=self.width)
        self.bottom_line = Line(width=self.width)
        self.left_line = Line(width=self.width)
        self.middle_line = Line(width=self.width)
        self.right_line = Line(width=self.width)

        self.add(self.color)
        self.add(self.top_line)
        self.add(self.bottom_line)
        self.add(self.left_line)
        self.add(self.middle_line)
        self.add(self.right_line)

        self.flattened = False

    def flatten(self):
        self.flattened = True

    def un_flatten(self):
        self.flattened = False

    def on_update(self, now_time):
        win_size = Window.size
        marker_w = win_size[0] * marker_width
        marker_h = win_size[1] * marker_height

        time_dif = self.time - now_time
        mark = time_to_xpos(time_dif, win_size)

        if self.flattened:
            height_int = 2
        else:
            height_int = self.height

        height = (height_int * build_height * win_size[1]) + win_size[1] * ground_h

        self.marker.size = (marker_w, marker_h)
        self.marker.pos = (mark - (1 / 2) * marker_w, height - marker_h)

        self.top_line.points = [mark - (1 / 2) * marker_w + self.width, height - self.width,
                                mark + (1 / 2) * marker_w - self.width, height - self.width]
        self.bottom_line.points = [mark - (1 / 2) * marker_w + self.width, height - marker_h + self.width,
                                   mark + (1 / 2) * marker_w - self.width, height - marker_h + self.width]
        self.left_line.points = [mark - (1 / 2) * marker_w + self.width, height - self.width,
                                 mark - (1 / 2) * marker_w + self.width, height - marker_h + self.width]
        self.middle_line.points = [mark, height - self.width,
                                   mark, height - marker_h + self.width]
        self.right_line.points = [mark + (1 / 2) * marker_w - self.width, height - self.width,
                                  mark + (1 / 2) * marker_w - self.width, height - marker_h + self.width]

        # return - marker_width * win_size[0] <= mark - (1 / 2) * marker_w <= win_size[0] + marker_w
        return win_size[0] / 2 - marker_width * win_size[0] <= mark - (1 / 2) * marker_w <= win_size[0] + marker_w


class MarkerDisplay(InstructionGroup):
    def __init__(self, time, height):
        super(MarkerDisplay, self).__init__()
        self.time = time
        self.height = height
        self.color = Color(rgb=(1, 1, 1))
        self.marker = Rectangle(texture=Image('data/marker_texture.png').texture)
        self.add(self.color)
        self.add(self.marker)

        self.flattened = False

    def flatten(self):
        self.flattened = True

    def un_flatten(self):
        self.flattened = False

    def on_update(self, now_time):
        win_size = Window.size
        marker_w = win_size[0] * marker_width
        marker_h = win_size[1] * marker_height

        time_dif = self.time - now_time
        mark = time_to_xpos(time_dif, win_size)

        if self.flattened:
            height_int = 2
        else:
            height_int = self.height

        height = (height_int * build_height * win_size[1]) + win_size[1] * ground_h

        self.marker.size = (marker_w, marker_h)
        self.marker.pos = (mark - (1 / 2) * marker_w, height - marker_h)

        # return - marker_width * win_size[0] <= mark - (1 / 2) * marker_w <= win_size[0] + marker_w
        return win_size[0] / 2 - marker_width * win_size[0] <= mark - (1 / 2) * marker_w <= win_size[0] + marker_w


class PaintedBuildings(InstructionGroup):
    def __init__(self, prev_time, prev_height, cur_time, cur_height, next_time, next_height):
        super(PaintedBuildings, self).__init__()

        self.prev_time = prev_time
        self.prev_height = prev_height
        self.time = cur_time
        self.height = cur_height
        self.next_time = next_time
        self.next_height = next_height

        self.left_x = None
        self.right_x = None

        # percent of whiteness for buildings (initial coloring)
        index = random.randint(0, 8)

        random.seed(int(self.time))

        type = ['_rect_', '_vert_', '_hort_', '_round_']

        type_idx = random.randint(0, len(type))

        self.window_type = type[type_idx]

        file = 'data/building_textures/color' + self.window_type + str(index + 1) + '.png'

        self.color = Color(rgb=(1, 1, 1))
        self.color.a = 0
        self.size = None
        self.box = Rectangle(texture=Image(file).texture)

        self.add(self.color)
        self.add(self.box)

        self.flattened = False
        self.slowed_down = False
        self.sped_up = False
        self.success_time = None

        self.label = None

    def success(self, a, success_time):
        self.success_time = success_time
        self.color.a = a / 5 + 2 / 5

    def flatten(self):
        self.flattened = True

    def un_flatten(self):
        self.flattened = False

    def speed(self):
        self.sped_up = True

    def slowed(self):
        self.slowed_down = True

    def on_update(self, now_time):
        win_size = Window.size
        marker_w = win_size[0] * marker_width
        marker_h = win_size[1] * marker_height
        mark2gap = win_size[0] * mark_to_gap
        gap_w = win_size[0] * build_gap

        if self.prev_time is not None:
            # when self.time and now_time are the same, we should be at the middle
            # in seconds
            time_dif = self.time - now_time
            prev_time_dif = self.prev_time - now_time
            # x positions of middle of marker for current, previous, and next
            mark = time_to_xpos(time_dif, win_size)
            prev_mark = time_to_xpos(prev_time_dif, win_size)
            self.left_x = prev_mark + ((1 / 2) * marker_w) + mark2gap + gap_w
            self.right_x = mark + ((1 / 2) * marker_w) + mark2gap
            width = self.right_x - self.left_x
            if self.flattened:
                filename = 'data/building_textures/color' + self.window_type + str(2) + '.png'
                self.box.texture = Image(filename).texture
                height_int = 2
            else:
                height_int = self.height
            if self.slowed_down:
                filename = 'data/building_textures/color' + self.window_type + str(1) + '.png'
                self.box.texture = Image(filename).texture
            if self.sped_up:
                filename = 'data/building_textures/color' + self.window_type + str(4) + '.png'
                self.box.texture = Image(filename).texture
            self.size = (width, height_int * build_height * win_size[1])
            self.box.size = self.size
            self.box.pos = (self.left_x, win_size[1] * ground_h)
            # return True if position is visible in the window, False otherwise
            return - marker_width * win_size[0] <= self.right_x <= win_size[0] + width
        else:
            # when self.time and now_time are the same, we should be at the middle
            # in seconds
            time_dif = self.time - now_time
            # x positions of middle of marker for current, previous, and next
            mark = time_to_xpos(time_dif, win_size)

            prev_mark = time_to_xpos(-3, win_size)
            self.left_x = prev_mark + ((1 / 2) * marker_w) + mark2gap + gap_w

            self.right_x = mark + ((1 / 2) * marker_w) + mark2gap
            width = self.right_x - self.left_x

            if self.flattened:
                filename = 'data/building_textures/color' + self.window_type + str(2) + '.png'
                self.box.texture = Image(filename).texture
                height_int = 2
            else:
                height_int = self.height
            if self.slowed_down:
                filename = 'data/building_textures/color' + self.window_type + str(1) + '.png'
                self.box.texture = Image(filename).texture
            if self.sped_up:
                filename = 'data/building_textures/color' + self.window_type + str(4) + '.png'
                self.box.texture = Image(filename).texture
            self.size = (width, height_int * build_height * win_size[1])
            self.box.size = self.size
            self.box.pos = (self.left_x, win_size[1] * ground_h)
            # return True if position is visible in the window, False otherwise
            return - marker_width * win_size[0] <= self.right_x <= win_size[0] + width


class BuildingDisplay(InstructionGroup):
    def __init__(self, prev_time, prev_height, cur_time, cur_height, next_time, next_height):
        super(BuildingDisplay, self).__init__()

        self.prev_time = prev_time
        self.prev_height = prev_height
        self.time = cur_time
        self.height = cur_height
        self.next_time = next_time
        self.next_height = next_height

        self.left_x = None
        self.right_x = None

        # percent of whiteness for buildings (initial coloring)
        index = random.randint(0, 8)

        random.seed(int(self.time))

        type = ['_rect_', '_vert_', '_hort_', '_round_']

        type_idx = random.randint(0, len(type))

        self.window_type = type[type_idx]

        file = 'data/building_textures/grey' + self.window_type + str(index + 1) + '.png'

        self.size = None
        self.box = Rectangle(texture=Image(file).texture)

        self.add(self.box)

        self.flattened = False

        self.label = None
        self.hit = False
        self.hit_time = None
        self.passed = False
        self.passed_time = None

    # change to display this building being jumped on
    def on_land(self, time):
        self.hit = True
        self.hit_time = time

    # change to display a passed or missed building
    def on_pass(self, time):
        self.passed = True
        self.passed_time = time

    def flatten(self):
        self.flattened = True

    def un_flatten(self):
        self.flattened = False

    def on_update(self, now_time):
        win_size = Window.size
        marker_w = win_size[0] * marker_width
        marker_h = win_size[1] * marker_height
        mark2gap = win_size[0] * mark_to_gap
        gap_w = win_size[0] * build_gap

        if self.prev_time is not None:
            # when self.time and now_time are the same, we should be at the middle
            # in seconds
            time_dif = self.time - now_time
            prev_time_dif = self.prev_time - now_time

            # x positions of middle of marker for current, previous, and next
            mark = time_to_xpos(time_dif, win_size)
            prev_mark = time_to_xpos(prev_time_dif, win_size)

            self.left_x = prev_mark + ((1 / 2) * marker_w) + mark2gap + gap_w
            self.right_x = mark + ((1 / 2) * marker_w) + mark2gap

            width = self.right_x - self.left_x

            if self.flattened:
                height_int = 2
            else:
                height_int = self.height

            self.size = (width, height_int * build_height * win_size[1])
            self.box.size = self.size

            self.box.pos = (self.left_x, win_size[1] * ground_h)

            # return True if position is visible in the window, False otherwise
            return - marker_width * win_size[0] <= self.right_x <= win_size[0] + width
        else:
            # when self.time and now_time are the same, we should be at the middle
            # in seconds
            time_dif = self.time - now_time

            # x positions of middle of marker for current, previous, and next
            mark = time_to_xpos(time_dif, win_size)

            prev_mark = time_to_xpos(-3, win_size)

            self.left_x = prev_mark + ((1 / 2) * marker_w) + mark2gap + gap_w

            self.right_x = mark + ((1 / 2) * marker_w) + mark2gap

            width = self.right_x - self.left_x

            if self.flattened:
                height_int = 2
            else:
                height_int = self.height

            self.size = (width, height_int * build_height * win_size[1])
            self.box.size = self.size

            self.box.pos = (self.left_x, win_size[1] * ground_h)

            # return True if position is visible in the window, False otherwise
            return - marker_width * win_size[0] <= self.right_x <= win_size[0] + width


class PowerUp(InstructionGroup):
    def __init__(self, type, color, pos, size, audio_ctrl, building=None):
        super(PowerUp, self).__init__()

        self.audio_ctrl = audio_ctrl
        self.type = type
        self.pos = pos
        self.size = size
        self.color = Color(rgb=(1, 1, 1))
        self.texture_color = color
        if color == 1:
            self.texture = 'data/powerup_textures/blue_slow.png'
        elif color == 2:
            self.texture = 'data/powerup_textures/green_flat.png'
        else:
            self.texture = 'data/powerup_textures/red_fast.png'
        if building:
            self.color.a = 0.1
        self.icon = CEllipse(cpos=pos, csize=(size, size), texture=Image(self.texture).texture)
        self.add(self.color)
        self.add(self.icon)
        self.collected = False
        self.active_start = None
        self.cool_start = None
        self.collected_time = None
        self.init_pos = 0

        self.building = building
        if building:
            self.power_color = Color(rgb=(1, 1, 1))
            self.power_color.a = 1.0
            self.power = CEllipse(csize=(size, size), texture=Image(self.texture).texture)
            self.add(self.power_color)
            self.add(self.power)

    def activate(self, time):
        if self.collected:
            if not self.active_start and not self.cool_start:
                self.active_start = time
                self.color.a = 0.05
                if self.type in ['slow', 'fast']:
                    self.audio_ctrl.speed_toggle(self.type)
                else:
                    self.audio_ctrl.tracks[0].set_gain(0.2)
                    self.audio_ctrl.tracks[1].set_gain(0.8)
                    self.audio_ctrl.tracks[2].set_gain(0.2)
                    self.audio_ctrl.tracks[3].set_gain(1.0)

    def collect(self, now_time):
        self.collected = True
        self.collected_time = now_time
        self.init_pos = self.power.get_cpos()
        # self.color.a = 1.0
        # if self.building:
        #     self.power_color.a = 0

    def on_update(self, now_time):
        if self.building:
            win_size = Window.size
            self.power.set_cpos((self.building.right_x - marker_width * win_size[0],
                                 (self.building.height * build_height + ground_h) * win_size[1] + self.size / 2))
        if self.collected:
            # animation when collected
            if self.collected_time:
                frac = (now_time - self.collected_time) / 0.5
                x = frac * (self.pos[0] - self.init_pos[0]) + self.init_pos[0]
                y = frac * (self.pos[1] - self.init_pos[1]) + self.init_pos[1]
                self.power.set_cpos((x, y))
                if frac > 1:
                    self.collected_time = None
                    if self.building:
                        self.color.a = 1.0
                        self.power_color.a = 0.0
            # if power up is active and time has run out
            if self.active_start:
                if now_time - self.active_start > 15:
                    self.active_start = None
                    self.cool_start = now_time
                    if self.type == 'flat':
                        self.audio_ctrl.tracks[0].set_gain(1.0)
                        self.audio_ctrl.tracks[1].set_gain(1.0)
                        self.audio_ctrl.tracks[2].set_gain(1.0)
                    else:
                        self.audio_ctrl.speed_toggle(self.type)
            # if the power up is cooling down
            if self.cool_start:
                self.color.a = 0.05 + (now_time - self.cool_start) / 60
                # if power up has finished cooling down
                if now_time - self.cool_start > 30:
                    self.color.a = 1.0
                    self.cool_start = None

    def on_layout(self, win_size):
        # will adjust layout size soon!
        height = win_size[1]
        width = win_size[0]
        if self.texture_color == 1:
            frac = 0.25
        elif self.texture_color == 2:
            frac = 0.5
        else:
            frac = 0.75
        ymargin = 0.02 * Window.height
        xmargin = 0.3 * Window.width
        box_w = Window.width - 2 * xmargin
        box_h = Window.height * 0.15
        x = xmargin
        y = ymargin
        size = 0.05 * width
        self.icon.set_cpos((x + frac * box_w, y + box_h / 2))
        self.icon.set_csize((size, size))
        self.power.set_csize((size, size))


class PaletteBox(InstructionGroup):
    def __init__(self, x, y, box_w, box_h):
        super(PaletteBox, self).__init__()
        self.x = x
        self.y = y
        self.box_w = box_w
        self.box_h = box_h
        self.palette_box = Rectangle(size=(box_w, box_h), pos=(x, y),
                                     texture=Image('data/color_palette_texture.png').texture)
        self.add(Color((1, 1, 1)))
        self.add(self.palette_box)

    def on_update(self):
        pass

    def on_layout(self, win_size):
        # will adjust layout size soon!
        height = win_size[1]
        width = win_size[0]
        ymargin = 0.02 * height
        xmargin = 0.3 * width
        box_w = width - 2 * xmargin
        box_h = height * 0.15
        x = xmargin
        y = ymargin
        self.palette_box.pos = (x, y)
        self.palette_box.size = (box_w, box_h)
        self.palette_box.texture = Image('data/color_palette_texture.png').texture


class ScoreDisplay(InstructionGroup):
    def __init__(self):
        super(ScoreDisplay, self).__init__()
        self.score = CLabelRect(cpos=(Window.width * 0.85, Window.height * 0.9), text="Score: 0")
        self.lives = CLabelRect(cpos=(Window.width * 0.85, Window.height * 0.85), text="10 lives", font_size=30)
        self.combo = CLabelRect(cpos=(Window.width * 0.85, Window.height * 0.8), text="Combo: 0")
        self.add(Color(1, 1, 1))
        self.add(self.score)
        self.add(self.lives)
        self.add(self.combo)

    def on_update(self):
        pass

    def on_layout(self, win_size):
        # will adjust layout size soon!
        width = win_size[0]
        height = win_size[1]
        self.score.set_cpos((width * 0.85, height * 0.9))
        self.lives.set_cpos((width * 0.85, height * 0.85))
        self.combo.set_cpos((width * 0.85, height * 0.8))


class BackdropDisplay(InstructionGroup):
    def __init__(self, rainbow_level):
        super(BackdropDisplay, self).__init__()
        self.level = rainbow_level
        if rainbow_level == 0:
            self.file = 'data/backdrop no rainbow.png'
        elif rainbow_level == 1:
            self.file = 'data/backdrop 1 rainbow.png'
        elif rainbow_level == 2:
            self.file = 'data/backdrop 2 rainbow.png'
        elif rainbow_level == 3:
            self.file = 'data/backdrop 3 rainbow.png'
        elif rainbow_level == 4:
            self.file = 'data/backdrop 4 rainbow.png'
        elif rainbow_level == 5:
            self.file = 'data/backdrop 5 rainbow.png'
        elif rainbow_level == 6:
            self.file = 'data/backdrop 6 rainbow.png'
        else:
            self.file = 'data/backdrop 7 rainbow.png'

        self.height = Window.size[1]
        self.width = Window.size[0]
        self.backdrop_0 = CRectangle(size=(self.width, self.height), pos=(0, 0), texture=Image(self.file).texture)

        self.add(self.backdrop_0)

    def on_update(self, buildings_colored, total_builds):
        return (buildings_colored / total_builds >= self.level / 7) and (buildings_colored / total_builds < (self.level + 1)/7)

    def on_layout(self, win_size):
        self.height = win_size[1]
        self.width = win_size[0]
        self.backdrop_0.size = self.width, self.height
        self.backdrop_0.texture = Image(self.file).texture


class ScrollStreet(InstructionGroup):
    def __init__(self):
        super(ScrollStreet, self).__init__()
        self.width = Window.size[0]
        self.height = Window.size[1] * ground_h
        self.color = Color(rgb=(0.9, 0.9, 0.9))
        self.street = CRectangle(size=(self.width, self.height), pos=(0, 0))
        # texture=Image('data/scrollstreet.png').texture
        self.add(self.color)
        self.add(self.street)

    def on_update(self):
        pass

    def on_layout(self, win_size):
        self.width = win_size[0]
        self.height = win_size[1] * ground_h
        self.street.size = (self.width, self.height)
        # self.street.texture = Image('data/scrollstreet.png').texture


# Displays all game elements
class GameDisplay(InstructionGroup):
    def __init__(self, song_data, audio_ctrl, tutorial=None):
        super(GameDisplay, self).__init__()

        self.tutorial = tutorial
        self.audio_ctrl = audio_ctrl
        self.song_data = song_data
        self.song_data.make_clicks()
        self.build_data = song_data.builds

        height = Window.size[1]
        width = Window.size[0]

        self.buildings_colored = 0

        self.backdrops = [BackdropDisplay(i) for i in range(0, 8)]
        self.backdrop = self.backdrops[0]
        self.add(self.backdrop)

        self.street = ScrollStreet()
        self.add(self.street)

        self.builds = []
        self.painted = []

        for i in range(len(self.build_data)):
            if i == 0:
                # first building
                previous = None
                current = self.build_data[i]
                next = self.build_data[i + 1]
                self.builds.append(BuildingDisplay(None, None, current[0], current[1], next[0], next[1]))
                self.painted.append(PaintedBuildings(None, None, current[0], current[1], next[0], next[1]))
            elif i == len(self.build_data) - 1:
                # last building
                previous = self.build_data[i - 1]
                current = self.build_data[i]
                next = None
                self.builds.append(BuildingDisplay(previous[0], previous[1], current[0], current[1], None, None))
                self.painted.append(PaintedBuildings(previous[0], previous[1], current[0], current[1], None, None))
            else:
                previous = self.build_data[i - 1]
                current = self.build_data[i]
                next = self.build_data[i + 1]
                self.builds.append(BuildingDisplay(previous[0], previous[1], current[0], current[1], next[0], next[1]))
                self.painted.append(
                    PaintedBuildings(previous[0], previous[1], current[0], current[1], next[0], next[1]))

        self.total_builds = len(self.builds)

        for b in self.builds:
            self.add(b)
        for p in self.painted:
            self.add(p)

        self.markers = []
        self.marker_lines = []

        for b in self.build_data:
            self.markers.append(MarkerDisplay(*b))

        for m in self.markers:
            self.add(m)
            self.marker_lines.append(MarkerLines(m))

        for lines in self.marker_lines:
            self.add(lines)

        self.b_count = len(self.builds)
        self.p_count = len(self.painted)
        self.m_count = len(self.markers)
        self.l_count = len(self.marker_lines)

        # power-up active to flatten buildings to middle height
        self.flattened = False
        self.slowed = False
        self.speed = False

        # score display
        self.score_disp = ScoreDisplay()
        self.add(self.score_disp)

        # palette box
        ymargin = 0.02 * Window.height
        xmargin = 0.3 * Window.width
        box_w = Window.width - 2 * xmargin
        box_h = Window.height * 0.15
        x = xmargin
        y = ymargin
        self.palette = PaletteBox(x, y, box_w, box_h)
        self.add(self.palette)

        # palette icons in box
        self.power_icons = []
        pos = [(x + 0.25 * box_w, y + box_h / 2), (x + 0.5 * box_w, y + box_h / 2), (x + 0.75 * box_w, y + box_h / 2)]
        # color = [0 / 360, 105 / 360, 225 / 360, 60 / 360]
        color = [1, 2, 4]
        type = ['slow', 'flat', 'fast', 'default']
        size = 0.05 * Window.width
        if self.tutorial:
            i = 0
            build_idx = 21
            icon = PowerUp(type[i], color[i], pos[i], size, self.audio_ctrl, self.builds[build_idx])
            self.power_icons.append(icon)
            self.add(icon)
        else:
            for i in range(3):
                build_idx = random.randint(30, 50)
                icon = PowerUp(type[i], color[i], pos[i], size, self.audio_ctrl, self.builds[build_idx])
                self.power_icons.append(icon)
                self.add(icon)
        self.powerup_used = False

    # called by Player to update score
    def set_score(self, score):
        self.score_disp.score.set_text("Score: " + str(score))

    # called by Player to update combo
    def set_combo(self, combo):
        self.score_disp.combo.set_text("Combo: " + str(combo))

    # called by Player to update lives
    def set_lives(self, lives):
        self.score_disp.lives.set_text(str(lives) + " lives")

    def get_num_object(self):
        return len(self.children)

    def get_build_ypos(self):
        win_size = Window.size
        middle = win_size[0] / 2
        current_build = None
        for b in self.builds:
            left_x = b.left_x
            right_x = b.right_x
            if left_x is not None and right_x is not None:
                if left_x <= middle <= right_x:
                    current_build = b
                    break
        if current_build is not None:
            # return the height of the current building, the size of the building plus the ground margin
            if current_build.flattened:
                height_int = 2
            else:
                height_int = current_build.height
            return (height_int * win_size[1] * build_height) + (win_size[1] * ground_h)
        else:
            return win_size[1] * ground_h

    def on_layout(self, win_size):
        # will adjust layout size soon!
        for backdrop in self.backdrops:
            backdrop.on_layout(win_size)
        for powerup in self.power_icons:
            powerup.on_layout(win_size)
        self.palette.on_layout(win_size)
        self.score_disp.on_layout(win_size)
        self.street.on_layout(win_size)

    def on_update(self, now_time):
        for b in self.builds:
            if not b.on_update(now_time) and b in self.children and b.prev_time != None:
                self.children.remove(b)
                self.b_count -= 1
            elif b.on_update(now_time) and b not in self.children:
                if self.flattened:
                    b.flatten()
                else:
                    b.un_flatten()
                self.children.insert(1,b)
                self.b_count += 1
        for p in self.painted:
            if not p.on_update(now_time) and p in self.children:
                self.children.remove(p)
                self.p_count -=1
            elif p.on_update(now_time) and p not in self.children:
                if self.flattened:
                    p.flatten()
                else:
                    p.un_flatten()
                if self.slowed:
                    p.slowed()
                if self.speed:
                    p.speed()
                self.p_count += 1
                self.children.insert(1+self.b_count+self.m_count+self.l_count,p)
        for m in self.markers:
            if not m.on_update(now_time) and m in self.children:
                self.children.remove(m)
                self.m_count -= 1
            elif m.on_update(now_time) and m not in self.children:
                if self.flattened:
                    m.flatten()
                else:
                    m.un_flatten()
                self.m_count += 1
                self.children.insert(1+self.b_count,m)
        for lines in self.marker_lines:
            if not lines.on_update(now_time) and lines in self.children:
                self.children.remove(lines)
                self.l_count -= 1
            elif lines.on_update(now_time) and lines not in self.children:
                if self.flattened:
                    lines.flatten()
                else:
                    lines.un_flatten()
                self.l_count += 1
                self.children.insert(1+self.b_count+self.m_count,lines)
        for backdrop in self.backdrops:
            if not backdrop.on_update(self.buildings_colored, self.total_builds) and backdrop in self.children:
                self.children.remove(backdrop)
            elif backdrop.on_update(self.buildings_colored, self.total_builds) and backdrop not in self.children:
                self.children.insert(0,backdrop)

        self.children.sort(key=lambda x: (
            isinstance(x, BackdropDisplay), isinstance(x, BuildingDisplay), isinstance(x, MarkerDisplay),
            isinstance(x, MarkerLines), isinstance(x, PaintedBuildings), isinstance(x, ScrollStreet),
            isinstance(x, PaletteBox), isinstance(x, PowerUp)), reverse=True)
        # powerup active state check and update
        used = []
        for powerup in self.power_icons:
            if powerup.active_start:
                used.append(True)
            powerup.on_update(now_time)
        if any(used):
            self.powerup_used = True
        else:
            self.powerup_used = False
            self.flattened = False
            self.slowed = False
            self.speed = False


if __name__ == "__main__":
    run(MainWidget())
