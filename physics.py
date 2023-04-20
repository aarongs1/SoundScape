#physics.py

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, CEllipse, KFAnim, AnimGroup, CLabelRect

from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse
from kivy.core.image import Image

from random import random, randint
import numpy as np

time_span = 2.7  # time (in seconds) that spans the full horizontal width of the Window
build_width = 0.10  # horizontal width of building (as a proportion of window width)
build_height = 0.15
build_gap = 0.10
marker_width = 0.05

ground_h = 0.2  # height of ground from the bottom of screen (as proportion of window height)

slop_window = time_span*marker_width # slop window in either direction

gravity = np.array((0., -3*Window.height))

class Player(InstructionGroup):
    def __init__(self, song_data, audio_ctrl, game_display, pos, r, color):
        super(Player, self).__init__()

        self.song_data = song_data.get_clicks()
        self.audio_ctrl = audio_ctrl
        self.game_display = game_display
        self.song_remaining = self.song_data.copy()

        self.radius = r
        self.pos = np.array(pos, dtype=np.float64)
        self.vel = np.array((0,0), dtype=np.float64)

        self.height = 2
        self.floor = (self.height * build_height + ground_h) * Window.height

        self.color = Color(*color)
        self.add(self.color)

        self.circle = CEllipse(cpos=pos, csize=(2*r,2*r), segments = 40, texture=Image('data/sprite_run2.png').texture)
        self.add(self.circle)

        self.text_color = Color(1,1,1)
        self.add(self.text_color)
        self.text = CLabelRect(cpos=(pos[0],pos[1]+2*self.radius),text='',font_size=16)
        self.add(self.text)

        self.score = 0
        self.combo = 0
        self.lives = 10

        self.max_combo = 0
        self.perfects = 0
        self.excellents = 0
        self.decents = 0
        self.misses = 0

        self.playing = False

        self.window_height = Window.height

        self.jump_time = None
        self.jump_dur = None

        self.on_update(0)

    def set_vel(self, vel):
    	self.vel = (0,vel)

    def toggle(self):
        self.playing = not self.playing

    def add_life(self):
        self.lives += 1
        self.game_display.set_lives(self.lives)

    def is_dead(self):
        return self.lives <= 0

    def get_stats(self):
        return [self.score, self.max_combo, self.perfects, self.excellents, self.decents, self.misses]

    # called by MainWidget
    def on_button_down(self, jump):
        if self.pos[1] == self.game_display.get_build_ypos() + self.radius:
            curr_time = self.audio_ctrl.get_time()
            window_note = None # all of the notes within our slop window

            self.jump(jump)

            for note in self.song_remaining:
                if abs(note[0] - curr_time) <= slop_window:
                    window_note = note
            if window_note == None: # temporal miss
                self.combo = 0 # reset combo
                self.game_display.set_combo(self.combo)
                self.remove(self.text_color)
                self.remove(self.text)
                self.text_color = Color(1,0,0) # red
                self.add(self.text_color)
                self.text.set_text("Miss")
                self.add(self.text)
                self.misses += 1
            else: # we're within a building's marker
                next_note_idx = self.song_data.index(window_note) + 1
                build_idx = next_note_idx - 1
                if next_note_idx < len(self.song_data): # when we're at the end of the song, don't do anything
                    next_note = self.song_data[next_note_idx]
                    if (next_note[1] - window_note[1] == jump and self.game_display.flattened == False) or (self.game_display.flattened == True and jump == 0): # hit!
                        self.combo += 1
                        if self.combo > self.max_combo:
                            self.max_combo = self.combo
                        self.remove(self.text_color)
                        self.remove(self.text)
                        if abs(window_note[0] - curr_time) <= .025: # perfect!
                            self.score += 100
                            self.text_color = Color(0.8,0.8,1) # light blue
                            self.text.set_text("Perfect!")
                            self.perfects += 1
                            self.game_display.painted[build_idx].success(3, curr_time)
                            self.game_display.buildings_colored += 1

                        elif abs(window_note[0] - curr_time) <= .055: # excellent
                            self.score += 75
                            self.text_color = Color(1,1,0) # yellow
                            self.text.set_text("Excellent")
                            self.excellents += 1
                            self.game_display.painted[build_idx].success(2, curr_time)
                            self.game_display.buildings_colored += 1

                        elif abs(window_note[0] - curr_time) <= slop_window: # decent
                            self.score += 20
                            self.text_color = Color(0.75,1,0) # lime
                            self.text.set_text("Decent")
                            self.decents += 1
                            self.game_display.painted[build_idx].success(1, curr_time)
                            self.game_display.buildings_colored += 1

                        self.add(self.text_color)
                        self.add(self.text)

                        self.game_display.set_combo(self.combo)
                        self.game_display.set_score(self.score)
                        self.song_remaining.remove(window_note)
                    else: # wrong type of jump, miss
                        self.audio_ctrl.play_miss()
                        self.combo = 0
                        self.remove(self.text_color)
                        self.remove(self.text)
                        self.text_color = Color(1,0,0) # red
                        self.add(self.text_color)
                        self.text.set_text("Miss")
                        self.add(self.text)
                        self.misses += 1
                        self.game_display.set_combo(self.combo)
                        self.song_remaining.remove(window_note)

    def jump(self, type):
        self.jump_time = self.audio_ctrl.get_time()
        t_jump = (build_gap+marker_width)*time_span
        self.jump_dur = t_jump
        del_y = build_height*type*Window.height
        vel = (del_y-1/2*gravity[1]*t_jump**2)/t_jump #physics calculations to make sure the jump moves us the correct x distance
        self.circle.texture = Image('data/sprite_jump.png').texture
        self.set_vel(vel)

    def on_layout(self, win_size):
        curr_pos = self.pos
        self.radius = win_size[0]*0.0375
        self.circle.csize = (2*self.radius, 2*self.radius)
        self.pos = (win_size[0]/2, curr_pos[1]*win_size[1]/self.window_height)
        self.vel[1] = 0
        self.circle.cpos = self.pos
        self.window_height = win_size[1]
        print('layout')

    def on_update(self, dt):
        if self.playing:
            # animation for jump
            if self.jump_time:
                now = self.audio_ctrl.get_time()
                if now - self.jump_time > self.jump_dur:
                    self.circle.texture = Image('data/sprite_run2.png').texture
            if dt > 0.03:
                dt = 0.03

            # integrate accel to get vel
            self.vel += gravity * dt
            # integrate vel to get pos
            self.pos += self.vel * dt

            self.floor = self.game_display.get_build_ypos()
            # collision with floor
            if self.pos[1] - self.radius < self.floor and self.vel[1] < 0:
                if self.floor - (self.pos[1] - self.radius) > 0.02 * Window.height:
                    # print(self.floor)
                    # print(self.pos[1] - self.radius)
                    self.lives -= 1
                    self.game_display.set_lives(self.lives)
                    print('ouch')
                self.vel[1] = 0
                self.pos[1] = self.radius + self.floor

            self.circle.cpos = self.pos
            self.text.set_cpos((self.pos[0],self.pos[1]+2*self.radius))

            # check for passed gems
            curr_time = self.audio_ctrl.get_time()
            for note in self.song_remaining:
                if curr_time - note[0] > slop_window: # pass
                    self.audio_ctrl.play_miss()
                    self.song_remaining.remove(note)
                    # reset combo
                    self.combo = 0
                    self.remove(self.text_color)
                    self.remove(self.text)
                    self.text_color = Color(1,0,0) # red
                    self.add(self.text_color)
                    self.text.set_text("Miss")
                    self.add(self.text)
                    self.misses += 1
                    self.game_display.set_combo(self.combo)

            return True
