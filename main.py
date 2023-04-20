import sys, os
import numpy as np

sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator
from common.wavesrc import WaveBuffer, WaveFile
from common.gfxutil import topleft_label, resize_topleft_label, CLabelRect, KFAnim, AnimGroup, CRectangle
from common.screen import ScreenManager, Screen

from kivy.clock import Clock as kivyClock
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.core.image import Image
from kivy import metrics

from graphics_and_music import SongData, AudioController, GameDisplay
from physics import Player
from popups import PausePop, DeathPop, ScorePop

build_height = 0.15
ground_h = 0.2  # height of ground from the bottom of screen (as proportion of window height)

# metrics allows kivy to create screen-density-independent sizes.
# Here, 20 dp will always be the same physical size on screen regardless of resolution or OS.
# Another option is to use metrics.pt or metrics.sp. See https://kivy.org/doc/stable/api-kivy.metrics.html
font_sz = metrics.dp(24)
button_sz = metrics.dp(80)

class IntroScreen(Screen):
    def __init__(self, **kwargs):
        super(IntroScreen, self).__init__(always_update=False, **kwargs)

        self.title = CLabelRect(cpos=(Window.width/2,Window.height*3/4),text='Soundscape',font_size=80,font_name='Orbitron-Medium')
        self.canvas.add(self.title)

        self.button1 = Button(text='Start', font_size=font_sz, font_name='IBMPlexSans-Regular', size = (button_sz*2, button_sz), pos = (Window.width/2-button_sz, Window.height/2-button_sz*3/4))
        self.button1.bind(on_release= lambda x: self.switch_to('select'))
        self.add_widget(self.button1)

        self.button2 = Button(text='Instructions', font_size=font_sz, font_name='IBMPlexSans-Regular', size = (button_sz*2, button_sz), pos = (Window.width/2-button_sz, Window.height/2-button_sz*2))
        self.button2.bind(on_release= lambda x: self.switch_to('instructions'))
        self.add_widget(self.button2)


    # on_layout always gets called - even when a screen is not active.
    def on_layout(self, win_size):
        self.title.set_cpos((win_size[0]/2,win_size[1]*3/4))
        self.button1.pos = (Window.width/2-button_sz, Window.height/2-button_sz*3/4)
        self.button2.pos = (Window.width/2-button_sz, Window.height/2-button_sz*2)

class InstructionsScreen(Screen):
    def __init__(self, **kwargs):
        super(InstructionsScreen, self).__init__(**kwargs)

        self.title = CLabelRect(cpos=(Window.width/2,Window.height*5/6),text='Instructions',font_size=40,font_name='Orbitron-Medium')
        self.canvas.add(self.title)

        self.picture = CRectangle(size=(Window.width * 0.8, Window.height * 0.6),
                                  cpos=(Window.width / 2, Window.height / 2),
                                  texture=Image('data/instructions_slide.png').texture)
        self.canvas.add(self.picture)

        self.button = Button(text='Back', font_size=font_sz, size = (button_sz*2, button_sz), pos = (Window.width/2-button_sz, Window.height*1/12), font_name='IBMPlexSans-Regular')
        self.button.bind(on_release= lambda x: self.switch_to('intro'))
        self.add_widget(self.button)

    # on_layout always gets called - even when a screen is not active.
    def on_layout(self, win_size):
        self.title.set_cpos((win_size[0]/2,win_size[1]*5/6))
        self.button.pos = (Window.width/2-button_sz, Window.height*1/12)
        self.picture.set_cpos((Window.width / 2, Window.height / 2))
        self.picture.set_csize((Window.width * 0.8, Window.height * 0.6))

class SelectScreen(Screen):
    def __init__(self, **kwargs):
        super(SelectScreen, self).__init__(**kwargs)

        self.title = CLabelRect(cpos=(Window.width/2,Window.height*5/6),text='Level Select',font_size=40,font_name='Orbitron-Medium')
        self.canvas.add(self.title)

        self.button1 = Button(text='Tutorial', font_size=font_sz, size = (button_sz*2, button_sz), pos = (Window.width/2-button_sz, Window.height/2+button_sz*1/4), font_name='IBMPlexSans-Regular')
        self.button1.bind(on_release= lambda x: self.switch_to('tutorial'))
        self.add_widget(self.button1)

        self.button2 = Button(text='Level 1', font_size=font_sz, size = (button_sz*2, button_sz), pos = (Window.width/2-button_sz, Window.height/2-button_sz*5/4), font_name='IBMPlexSans-Regular')
        self.button2.bind(on_release= lambda x: self.switch_to('main'))
        self.add_widget(self.button2)

    def on_layout(self, win_size):
        self.title.set_cpos((win_size[0]/2,win_size[1]*5/6))
        self.button1.pos = (Window.width/2-button_sz, Window.height/2+button_sz*1/4)
        self.button2.pos = (Window.width/2-button_sz, Window.height/2-button_sz*5/4)

class TutorialScreen(Screen):
    def __init__(self, **kwargs):
        super(TutorialScreen, self).__init__(**kwargs)

        track1 = 'data/tutorial.wav'
        # track2 = 'data/drums.wav'
        # track3 = 'data/ambience.wav'
        # track4 = 'data/bass.wav'

        build_markers = 'data/tutorial_annotations.txt'

        print('1')
        self.audio_ctrl = AudioController([track1])
        print('2')
        self.song_data = SongData(build_markers)
        print('3')
        self.display = GameDisplay(self.song_data, self.audio_ctrl, tutorial=True)
        print('4')

        self.canvas.add(self.display)

        self.combo_max = 19
        self.score_max = 1900

        r = Window.width*0.0375


        p = (Window.width/2,Window.height*(2*build_height + ground_h)+r)
        c = (1, 1, 1)

        self.bub = Player(self.song_data,self.audio_ctrl,self.display,p,r,c) # character's name is bub (short for bubble, temp name)
        self.canvas.add(self.bub)
        self.bub.toggle()

        # pause window setup
        self.pause_pop = None
        self.paused = False

        # death window setup
        self.death_pop = None
        self.ded = False

        # score window setup
        self.score_pop = None
        self.finished = False

        self.tutorial_box = Rectangle(size=(Window.width*0.3, Window.height*0.2), pos=(Window.width*0.3, Window.height*0.2), texture=Image('data/tutorial_instructions/jump_same.png').texture)

        self.pause_w = 0
        self.pause_s = 0
        self.pause_d = 0
        self.pause_y = 0
        self.pause_rainbow = 0

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            if self.ded == False and self.finished == False:
                self.audio_ctrl.toggle()
                self.bub.toggle()

                if self.paused:
                    self.canvas.remove(self.pause_pop)
                    self.paused = False
                else:
                    self.pause_pop = PausePop()
                    self.canvas.add(self.pause_pop)
                    self.paused = True

        if keycode[1] == 'w':
            if self.pause_w == 1:
                self.pause_w = 2
                self.audio_ctrl.toggle()
                self.bub.toggle()

        if keycode[1] == 's':
            if self.pause_s == 1:
                self.pause_s = 2
                self.audio_ctrl.toggle()
                self.bub.toggle()
            if self.pause_s == 3:
                self.pause_s = 4
                self.audio_ctrl.toggle()
                self.bub.toggle()
                self.canvas.remove(self.tutorial_box)

        if keycode[1] == 'd':
            if self.pause_d == 1:
                self.pause_d = 2
                self.audio_ctrl.toggle()
                self.bub.toggle()

        if keycode[1] == 'y':
            if self.pause_y == 1:
                self.pause_y = 2
                self.audio_ctrl.toggle()
                self.bub.toggle()
                self.canvas.remove(self.tutorial_box)

        if keycode[1] == 'r':
            tut = sm.screens[3]
            sm.screens.remove(tut)
            sm.screens.insert(3,TutorialScreen(name='tutorial'))
            sm.switch_to('tutorial')

        if keycode[1] == 't':
            tut = sm.screens[3]
            sm.screens.remove(tut)
            sm.screens.insert(3,TutorialScreen(name='tutorial'))
            sm.switch_to('intro')


        button_idx = lookup(keycode[1], 'yui', (0,1,2))
        if button_idx != None and not self.display.powerup_used:
            now = self.audio_ctrl.get_time()
            # i flattens the buildings
            self.display.power_icons[button_idx].activate(now)
            if button_idx == 2:
                self.display.speed = True
                self.bub.add_life()
            if button_idx == 1:
                self.display.flattened = True
            if button_idx == 0:
                self.display.slowed = True

            print(self.display.power_icons[button_idx].type)

        # button down
        button_idx = lookup(keycode[1], '1234', (0, 1, 2, 3))
        if button_idx != None:
            print('down', button_idx)
            # mute/unmute track
            self.audio_ctrl.mute_track(button_idx)

        # player jump
        if keycode[1] in 'wsd':
            jump = lookup(keycode[1],'wsd',(1,-1,0)) # w is up, s is down, d is forward
            self.bub.on_button_down(jump)

    # handle changing displayed elements when window size changes
    def on_layout(self, win_size):
        self.bub.on_layout(win_size)
        if self.death_pop:
            self.death_pop.on_layout(win_size)
        if self.pause_pop:
            self.pause_pop.on_layout(win_size)
        if self.score_pop:
            self.score_pop.on_layout(win_size)
        self.display.on_layout(win_size)

    def on_update(self):
        self.audio_ctrl.on_update()
        now = self.audio_ctrl.get_time()
        self.display.on_update(now)
        if now > 2 and self.pause_d == 0:
            self.pause_d = 1
            self.canvas.add(self.tutorial_box)
            self.audio_ctrl.toggle()
            self.bub.toggle()
        if now > 3 and self.pause_w == 0:
            self.pause_w = 1
            self.tutorial_box.texture = Image('data/tutorial_instructions/jump_tall.png').texture
            self.audio_ctrl.toggle()
            self.bub.toggle()
        if now > 4 and self.pause_s == 0:
            self.pause_s = 1
            self.tutorial_box.texture = Image('data/tutorial_instructions/jump_short.png').texture
            self.audio_ctrl.toggle()
            self.bub.toggle()
        if now > 5 and self.pause_s == 2:
            self.pause_s = 3
            self.tutorial_box.texture = Image('data/tutorial_instructions/jump_green.png').texture
            self.audio_ctrl.toggle()
            self.bub.toggle()
        if now > 11 and self.pause_rainbow == 0:
            self.pause_rainbow = 1
            self.tutorial_box.texture = Image('data/tutorial_instructions/rainbow.png').texture
            self.canvas.add(self.tutorial_box)
        if now > 20 and self.pause_rainbow == 1:
            self.pause_rainbow = 2
            self.canvas.remove(self.tutorial_box)

        if now > 24.5 and self.pause_y == 0:
            self.pause_y = 1
            self.tutorial_box.texture = Image('data/tutorial_instructions/powerup.png').texture
            self.canvas.add(self.tutorial_box)
            self.audio_ctrl.toggle()
            self.bub.toggle()

        # update player, based on time per frame
        self.bub.on_update(kivyClock.frametime)

        #check if player has collected a PowerUp
        for power in self.display.power_icons[:3]:
            dist = np.linalg.norm(np.array(power.power.get_cpos()) - np.array(self.bub.pos))
            if dist < power.size/2:
                power.collect(now)

        # check if dead
        if self.bub.is_dead() and self.ded == False:
            # pause song
            self.audio_ctrl.toggle()
            self.bub.toggle()
            # show death screen
            self.death_pop = DeathPop()
            self.canvas.add(self.death_pop)
            self.ded = True

        # check if won
        if self.audio_ctrl.get_time() >= 61.8 and self.finished == False:
            print("finished!")
            # pause song
            self.audio_ctrl.toggle()
            self.bub.toggle()
            # show score screen
            stats = self.bub.get_stats()
            self.score_pop = ScorePop()
            self.score_pop.set_text(*stats, self.combo_max, self.score_max)
            self.canvas.add(self.score_pop)
            self.finished = True


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        track1 = 'data/lead_violin.wav'
        track2 = 'data/drums.wav'
        track3 = 'data/ambience.wav'
        track4 = 'data/bass.wav'

        build_markers = 'data/annotations.txt'

        print('1')
        self.audio_ctrl = AudioController([track1, track2, track3, track4])
        print('2')
        self.song_data = SongData(build_markers)
        print('3')
        self.display = GameDisplay(self.song_data, self.audio_ctrl)
        print('4')

        self.canvas.add(self.display)

        self.combo_max = 251 # best combo one can get
        self.score_max = 25100 # best score one can get

        r = Window.width*0.0375
        p = (Window.width/2,Window.height*(2*build_height + ground_h)+r)
        c = (1, 1, 1)

        self.bub = Player(self.song_data,self.audio_ctrl,self.display,p,r,c) # character's name is bub (short for bubble, temp name)
        self.canvas.add(self.bub)
        self.bub.toggle()

        # pause window setup
        self.pause_pop = None
        self.paused = False

        # death window setup
        self.death_pop = None
        self.ded = False

        # score window setup
        self.score_pop = None
        self.finished = False

        # self.info = topleft_label()
        # self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            if self.ded == False and self.finished == False:
                self.audio_ctrl.toggle()
                self.bub.toggle()

                if self.paused:
                    self.canvas.remove(self.pause_pop)
                    self.paused = False
                else:
                    self.pause_pop = PausePop()
                    self.canvas.add(self.pause_pop)
                    self.paused = True

        if keycode[1] == 'r':
            main = sm.screens[4]
            sm.screens.remove(main)
            sm.screens.insert(4,MainScreen(name='main'))
            sm.switch_to('main')

        if keycode[1] == 't':
            main = sm.screens[4]
            sm.screens.remove(main)
            sm.screens.insert(4,MainScreen(name='main'))
            sm.switch_to('intro')


        button_idx = lookup(keycode[1], 'yui', (0,1,2))
        if button_idx != None and not self.display.powerup_used:
            now = self.audio_ctrl.get_time()
            # i flattens the buildings
            self.display.power_icons[button_idx].activate(now)
            if button_idx == 2:
                self.display.speed = True
                self.bub.add_life()
            if button_idx == 1:
                self.display.flattened = True
            if button_idx == 0:
                self.display.slowed = True

            print(self.display.power_icons[button_idx].type)

        # button down
        button_idx = lookup(keycode[1], '1234', (0, 1, 2, 3))
        if button_idx != None:
            print('down', button_idx)
            # mute/unmute track
            self.audio_ctrl.mute_track(button_idx)

        # player jump
        if keycode[1] in 'wsd':
            jump = lookup(keycode[1],'wsd',(1,-1,0)) # w is up, s is down, d is forward
            self.bub.on_button_down(jump)

    # handle changing displayed elements when window size changes
    def on_layout(self, win_size):
        self.bub.on_layout(win_size)
        if self.death_pop:
            self.death_pop.on_layout(win_size)
        if self.pause_pop:
            self.pause_pop.on_layout(win_size)
        if self.score_pop:
            self.score_pop.on_layout(win_size)
        self.display.on_layout(win_size)

    def on_update(self):
        self.audio_ctrl.on_update()
        now = self.audio_ctrl.get_time()
        self.display.on_update(now)

        # update player, based on time per frame
        self.bub.on_update(kivyClock.frametime)
        # if kivyClock.frametime > 0.02:
        #     print(kivyClock.frametime)

        #check if player has collected a PowerUp
        for power in self.display.power_icons[:3]:
            dist = np.linalg.norm(np.array(power.power.get_cpos()) - np.array(self.bub.pos))
            if dist < power.size/2:
                power.collect(now)

        # check if dead
        if self.bub.is_dead() and self.ded == False:
            # pause song
            self.audio_ctrl.toggle()
            self.bub.toggle()
            # show death screen
            self.death_pop = DeathPop()
            self.canvas.add(self.death_pop)
            self.ded = True

        # check if won
        if self.audio_ctrl.get_time() >= 190.8 and self.finished == False:
            print("finished!")
            # pause song
            self.audio_ctrl.toggle()
            self.bub.toggle()
            # show score screen
            stats = self.bub.get_stats()
            self.score_pop = ScorePop()
            self.score_pop.set_text(*stats, self.combo_max, self.score_max)
            self.canvas.add(self.score_pop)
            self.finished = True

        # self.info.text = 'objects:%d' % len(self.display.children)
        # self.info.text += '\nfps:%d' % kivyClock.get_fps()


# create the screen manager
sm = ScreenManager()

# add all screens to the manager. By default, the first screen added is the current screen.
# each screen must have a name argument (so that switch_to() will work).
# If screens need to share data between themselves, feel free to pass in additional arguments
# like a shared data class or they can even know directly about each other as needed.
sm.add_screen(IntroScreen(name='intro'))
sm.add_screen(InstructionsScreen(name='instructions'))
sm.add_screen(SelectScreen(name='select'))
sm.add_screen(TutorialScreen(name='tutorial'))
sm.add_screen(MainScreen(name='main'))

run(sm)
