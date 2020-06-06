#encoding: utf-8
import os
import time
import numpy as np
import LED
import pandas as pd
import fixedsizes as fx
import pickle
import lirc

def blank_display():
	for i in range(LED.DRIVER_COUNT*24):
		LED.tlc5947[i] = 0
	LED.tlc5947.write()

def apply_pattern(filename):
	global LED, pattern_selected, old_ircode, new_ircode
	if pattern_selected != filename:
		pattern_selected = filename
	blank_display()
	Render = 0
	f=open(filename,'rb')
	Render = pickle.load(f)
	f.close
	Form = np.shape(Render)
	Render.shape = (int(Form[0]/960),960)
	Form = np.shape(Render)
	LengthFrame = Form[1]
	NumberFrames =Form[0]
	for FrameCount in range(0,NumberFrames):
		codeIR = lirc.nextcode()
		if codeIR != []:
			new_ircode = codeIR[0]
			old_ircode = "update"
			pattern_selected = ""
			blank_display()
			break
		#Frame = Render[FrameCount]
		for FrameAdress in range(0,LengthFrame):
			LED.tlc5947[FrameAdress]=Render[FrameCount,FrameAdress]
		LED.tlc5947.write()
	blank_display()
	
def act_on_code(code):
	if code == "KEY_UP":
		apply_pattern("test.rnd")
	elif code == "KEY_DOWN":
		apply_pattern("pattern3.rnd")
	elif code == "KEY_LEFT":
		apply_pattern("pattern4.rnd")
	elif code == "KEY_RIGHT":
		apply_pattern("pattern2.rnd")
	elif code == "KEY_OK":
		print(str(code))
	elif code == "KEY_MENU":
		print(str(code))
	elif code == "KEY_PLAYPAUSE":
		print(str(code))

if __name__ == '__main__':
	global Render, LED, pattern_selected, old_ircode, new_ircode
	
	pattern_selected = ""
	old_ircode = ""
	new_ircode = ""

	
	#initialisieren GPIO's und LED's
	LED.Init_Panel()
	
	sockid=lirc.init("appleremote", blocking = False)
	try:
		apply_pattern("pattern0.rnd")
		pattern_selected = ""
	except Exception as e:
		print(str(e.args))
	while True:
		try:
			old_ircode = new_ircode
			codeIR = lirc.nextcode()
			if codeIR != []:
				new_ircode = codeIR[0]
				act_on_code(new_ircode)
			elif pattern_selected != "":
				apply_pattern(pattern_selected)
			if old_ircode == "update":
				act_on_code(new_ircode)
			time.sleep(0.02)
		except KeyboardInterrupt:
			raise
		except Exception as e:
			print(str(e.args))
			pattern_selected = ""
			old_ircode = ""
			new_ircode = ""
	