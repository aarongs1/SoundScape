import sys, os
import numpy as np

sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, resize_topleft_label, CLabelRect, KFAnim, AnimGroup, CRectangle

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window

class PausePop(InstructionGroup):
    def __init__(self):
        super(PausePop, self).__init__()
        self.window_color = Color(0,0,0)
        self.window = CRectangle(size=(Window.width/2, Window.height/2), cpos=(Window.width/2, Window.height/2))
        self.text_color = Color(1,1,1)
        self.title = CLabelRect(cpos=(Window.width/2,Window.height*2/3),text='Paused',font_size=30,font_name='Orbitron-Medium')
        self.text = CLabelRect(cpos=(Window.width/2, Window.height*1/3),text='Press [p] to unpause',font_size=18,font_name='IBMPlexSans-Regular')
        self.text2 = CLabelRect(cpos=(Window.width/2, Window.height*5/12),text='Press [r] to restart',font_size=18,font_name='IBMPlexSans-Regular')
        self.text3 = CLabelRect(cpos=(Window.width/2, Window.height*1/2),text='Press [t] to go back to the title screen',font_size=18,font_name='IBMPlexSans-Regular')

        self.add(self.window_color)
        self.add(self.window)
        self.add(self.text_color)
        self.add(self.title)
        self.add(self.text)
        self.add(self.text2)
        self.add(self.text3)
        
    def on_layout(self, win_size):
    	self.window.cpos=(win_size[0]/2, win_size[1]/2)
    	self.window.size=(win_size[0]/2, win_size[1]/2)
    	self.title.set_cpos((win_size[0]/2, win_size[1]*2/3))
    	self.text.set_cpos((win_size[0]/2, win_size[1]*1/3))
    	self.text2.set_cpos((win_size[0]/2, win_size[1]*5/12))
    	self.text3.set_cpos((win_size[0]/2, win_size[1]/2))

class DeathPop(InstructionGroup):
	def __init__(self):
		super(DeathPop, self).__init__()
		
		self.window_color = Color(0,0,0)
		self.window = CRectangle(size=(Window.width*2/3, Window.height*2/3), cpos=(Window.width/2, Window.height/2))
		self.text_color = Color(1,1,1)
		self.title = CLabelRect(cpos=(Window.width/2,Window.height*2/3),text='You Died...',font_size=30,font_name='Orbitron-Medium')
		self.text = CLabelRect(cpos=(Window.width/2, Window.height*2/5),text='Press [r] to try again',font_size=18,font_name='IBMPlexSans-Regular')
		self.text2 = CLabelRect(cpos=(Window.width/2, Window.height*1/2),text='Press [t] to go back to the title screen',font_size=18,font_name='IBMPlexSans-Regular')

		self.add(self.window_color)
		self.add(self.window)
		self.add(self.text_color)
		self.add(self.title)
		self.add(self.text)
		self.add(self.text2)

	def on_layout(self, win_size):
		self.window.cpos=(win_size[0]/2, win_size[1]/2)
		self.window.size=(win_size[0]*2/3, win_size[1]*2/3)
		self.title.set_cpos((win_size[0]/2, win_size[1]*2/3))
		self.text.set_cpos((win_size[0]/2, win_size[1]*2/5))
		self.text2.set_cpos((win_size[0]/2, win_size[1]*1/2))

class ScorePop(InstructionGroup):
	def __init__(self):
		super(ScorePop, self).__init__()

		self.window_color = Color(1,1,1)
		self.window = CRectangle(size=(Window.width*3/4, Window.height*3/4), cpos=(Window.width/2, Window.height/2), texture=Image('data/end_backdrop_city.png').texture)
		self.text_color = Color(0,0,0)
		self.title = CLabelRect(cpos=(Window.width/2,Window.height*3/4),text='You Won!',font_size=40,font_name='Orbitron-Medium')
		self.text = CLabelRect(cpos=(Window.width/2, Window.height*1/5),text='Press [t] to go back to the title screen',font_size=18,font_name='IBMPlexSans-Regular')
		self.max_combo = CLabelRect(cpos=(Window.width/2, Window.height*10/15),text='Max Combo: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.score = CLabelRect(cpos=(Window.width/2, Window.height*5/15),text='Score: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.grade = CLabelRect(cpos=(Window.width/2, Window.height*4/15),text='Grade: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.perfect_color = Color(0.4,0.4,1)
		self.perfect_text = CLabelRect(cpos=(Window.width/2, Window.height*9/15),text='Perfects: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.excellent_color = Color(1,1,0)
		self.excellent_text = CLabelRect(cpos=(Window.width/2, Window.height*8/15),text='Excellents: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.decent_color = Color(0.6,0.8,0)
		self.decent_text = CLabelRect(cpos=(Window.width/2, Window.height*7/15),text='Decents: ', font_size=20,font_name='IBMPlexSans-Regular')
		self.miss_color = Color(1,0,0)
		self.miss_text = CLabelRect(cpos=(Window.width/2, Window.height*6/15),text='Misses: ', font_size=20,font_name='IBMPlexSans-Regular')

		self.add(self.window_color)
		self.add(self.window)
		self.add(self.text_color)
		self.add(self.title)
		self.add(self.text)
		self.add(self.max_combo)
		self.add(self.score)
		self.add(self.grade)
		self.add(self.perfect_color)
		self.add(self.perfect_text)
		self.add(self.excellent_color)
		self.add(self.excellent_text)
		self.add(self.decent_color)
		self.add(self.decent_text)
		self.add(self.miss_color)
		self.add(self.miss_text)

	def set_text(self, score, max_combo, perfects, excellents, decents, misses, combo_max, score_max):
		self.score.set_text("Score: " + str(score))
		self.max_combo.set_text("Max Combo: " + str(max_combo))
		self.perfect_text.set_text("Perfect: " + str(perfects))
		self.excellent_text.set_text("Excellents: " + str(excellents))
		self.decent_text.set_text("Decents: " + str(decents))
		self.miss_text.set_text("Misses: " + str(misses))

		# grade calculation
		if score/score_max > 0.95:
			grade = "A+"
		elif score/score_max > 0.9:
			grade = "A"
		elif score/score_max > 0.8:
			grade = "B"
		elif score/score_max > 0.65:
			grade = "C"
		elif score/score_max > 0.5:
			grade = "D"
		else:
			grade = "D-"

		if max_combo >= combo_max:
			grade += ", Full Combo!"

		self.grade.set_text("Grade: " + grade)


	def on_layout(self, win_size):
		self.window.cpos=(win_size[0]/2, win_size[1]/2)
		self.window.size=(win_size[0]*3/4, win_size[1]*3/4)
		self.window.texture=Image('data/end_backdrop_city.png').texture
		self.title.set_cpos((win_size[0]/2, win_size[1]*3/4))
		self.text.set_cpos((win_size[0]/2, win_size[1]*1/5))
		self.perfect_text.set_cpos((win_size[0]/2, win_size[1]*9/15))
		self.excellent_text.set_cpos((win_size[0]/2, win_size[1]*8/15))
		self.decent_text.set_cpos((win_size[0]/2, win_size[1]*7/15))
		self.miss_text.set_cpos((win_size[0]/2, win_size[1]*6/15))
		self.grade.set_cpos((win_size[0]/2, win_size[1]*4/15))
		self.score.set_cpos((win_size[0]/2, win_size[1]*5/15))
		self.max_combo.set_cpos((win_size[0]/2, win_size[1]*10/15))