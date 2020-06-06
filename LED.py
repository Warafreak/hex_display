#encoding: utf-8
# first do this: https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
# sudo pip3 install adafruit-circuitpython-tlc5947

import time
import board
import busio
import digitalio
import numpy as np
import adafruit_tlc5947
import RPi.GPIO as GPIO
import threading
from math import sin , cos, pi, sqrt, atan2
import fixedsizes as fx
import array_builder as ab
import pickle

#Debug-Flag erlaubt Ausgabe von Debug-Informationen auf das erste Panel
Debug = True


RELAIS_1_GPIO = 4
GPIO.setmode(GPIO.BCM) # GPIO Nummern statt Board Nummern
GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # GPIO Modus zuweisen

# Initialize SPI bus.
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)

# Initialize TLC5947
DRIVER_COUNT = 40		# change this to the number of drivers you have chained
LATCH = digitalio.DigitalInOut(board.D25)
tlc5947 = adafruit_tlc5947.TLC5947(spi,LATCH,auto_write=False,num_drivers=DRIVER_COUNT)


# reference table for linear brightness correction
Brightness_table = np.array([0, 0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 19, 22, 25, 28, 32, 37, 42, 48, 55, 63, 72, 82, 94, 107, 122, 139, 158, 180, 205, 234, 266, 303, 346, 394, 449, 511, 582, 663, 755, 860, 980, 1116, 1271, 1447, 1648, 1877, 2138, 2434, 2773, 3157, 3596, 4095])


	#Shadow-memory for LED-matrix
#Shadow-memory contains a brightness-information between 0 and 63
#Variable represents the panel 1:1
Shadow_LED = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=int)

#array containing the mapping of channel to position
hex_lp = np.array([[-1,1,7,-1],[3,0,4,5],[21,2,6,11],[20,22,10,8],[23,18,14,9],[17,16,12,15],[-1,19,13,-1]],dtype=int)

#map for a rotation of the hexagon by 60 degrees counterclockwise
shift_map = np.array([[0,7,11,3],[2,6,15,19],[1,10,14,23],[5,9,18,22],[4,13,17,26],[8,12,21,25],[24,16,20,27]],dtype=int)

    
def debug(Level):
	global Debug
	if Debug == True:
		tlc5947[Level]=100

def Blank_Panel(Blank):
	if Blank == True:
		GPIO.output(RELAIS_1_GPIO, GPIO.HIGH) # an
	else:
		GPIO.output(RELAIS_1_GPIO, GPIO.LOW) # aus
				
class JOB:

	def __init__(self):
		self.__Job_number = 0
		self.__Activity = "Perform"
		self.__Fade_in = 0
		self.__Fade_out = 0
		self.__Duration = 0
		self.__Act_Rotation=0
		self.__Overwrite_Behavior = 0
		self.__Act_X=0
		self.__Act_Y=0
		self.__Start_X = 0
		self.__Start_Y = 0
		self.__Rotation=0
		self.__Pivot_X = 0
		self.__Pivot_Y = 0
		self.__Move_X=0
		self.__Move_Y=0
		self.__Job_Done = False
		self.__Next_Job_Due_In = 0
		self.__Cycles_Elapsed = 0
		self.__Target_Bright = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=float)
		self.__Actual_Bright = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=float)
		self.__Step_Bright = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=float)
		
		
	def getJob_number(self):  
		return self.__Job_number
	
	def setJob_number(self, Job_number):
		self.__Job_number= Job_number

	def getActivity(self):  
		return self.__Activity
	
	def setJob_Activity(self, Activity):
		self.__Activity= Activity
		
	def getFade_in(self):  
		return self.__Fade_in
	
	def setFade_in(self, Fade_in):
		self.__Fade_in = Fade_in
		
	def getFade_out(self):
		return self.__Fade_out
	
	def setFade_out(self, Fade_out):
		self.__Fade_out = Fade_out
		
	def getDuration(self):
		return self.__Duration
	
	def setDuration(self, Duration):
		self.__Duration = Duration
		
	def getJob_Done(self):
		return self.__Job_Done
	
	def setJob_Done(self, Job_Done):
		self.__Job_Done = Job_Done
		
	def getNext_Job_Due_In(self):
		return self.__Next_Job_Due_In
	
	def setNext_Job_Due_In(self, Next_Job_Due_In):
		self.__Next_Job_Due_In = Next_Job_Due_In
		
	def getCycles_Elapsed(self):
		return self.__Cycles_Elapsed
	
	def setCycles_Elapsed(self, Cycles):
		self.__Cycles_Elapsed = Cycles

	def getTarget_Bright(self):
		return self.__Target_Bright
	
	def setTarget_Bright(self, Target_Bright):
		self.__Target_Bright = Target_Bright

	def getActual_Bright(self):
		return self.__Actual_Bright
	
	def setActual_Bright(self,Actual_Bright):
		self.__Actual_Bright = Actual_Bright

	def getStep_Bright(self):
		return self.__Step_Bright
	
	def setStep_Bright(self,Step_Bright):
		self.__Step_Bright = Step_Bright

	def getRotation(self):
		return self.__Rotation
	
	def setRotation(self,Rotation):
		self.__Rotation = Rotation

	def getPivot_X(self):
		return self.__Pivot_X
	
	def setPivot_X(self,Pivot_X):
		self.__Pivot_X = Pivot_X

	def getPivot_Y(self):
		return self.__Pivot_Y
	
	def setPivot_Y(self,Pivot_Y):
		self.__Pivot_Y = Pivot_Y

	def getMove_X(self):
		return self.__Move_X
	
	def setMove_X(self,Move_X):
		self.__Move_X = Move_X

	def getMove_Y(self):
		return self.__Move_Y
	
	def setMove_Y(self,Move_Y):
		self.__Move_Y = Move_Y

	def getAct_X(self):
		return self.__Act_X
	
	def setAct_X(self,Act_X):
		self.__Act_X = __Act_X

	def getAct_Y(self):
		return self.__Act_Y
	
	def setAct_Y(self,Act_Y):
		self.__Act_Y = Act_Y

	def getAct_Rotation(self):
		return self.__Act_Rotation
	
	def setAct_Rotation(self,Act_Rotation):
		self.__Act_Rotation = Act_Rotation

	def getStart_X(self):
		return self.__Start_X
	
	def setStart_X(self,Start_X):
		self.__Start_X = Start_X

	def getStart_Y(self):
		return self.__Start_Y
	
	def setStart_Y(self,Start_Y):
		self.__Start_Y = Start_Y
		
	def Move(self, Init):
		if Init == True:
			self.__Act_X = self.__Start_X
			self.__Act_Y = self.__Start_Y
		else:
			self.__Act_X += round(self.__Move_X,2)
			self.__Act_Y += round(self.__Move_Y,2)
		
	def Rotate(self, Init):
		if  Init == True:
			self.__Act_Rotation = 0
		else:
			self.__Act_Rotation += self.__Rotation

	Fade_in = property(getFade_in, setFade_in)
	Fade_out = property(getFade_out, setFade_out)
	Duration = property(getDuration, setDuration)
	Job_Done = property(getJob_Done, setJob_Done)
	Next_Job_Due_In = property(getNext_Job_Due_In,setNext_Job_Due_In)
	Cycles_Elapsed = property(getCycles_Elapsed, setCycles_Elapsed)
	Target_Bright = property(getTarget_Bright, setTarget_Bright)
	Actual_Bright = property(getActual_Bright, setActual_Bright)
	Step_Bright = property(getStep_Bright, setStep_Bright)
	Rotation = property(getRotation, setRotation)
	Pivot_X = property(getPivot_X, setPivot_X)
	Pivot_Y = property(getPivot_Y, setPivot_Y)
	Move_X = property(getMove_X, setMove_X)
	Move_Y = property(getMove_Y, setMove_Y)
	Start_X = property(getStart_X, setStart_X)
	Start_Y = property(getStart_Y, setStart_Y)
	Act_X = property(getAct_X, setAct_X)
	Act_Y = property(getAct_Y, setAct_Y)
	Act_Rotation = property(getAct_Rotation, setAct_Rotation)
	
def TransX(Job, x,y):
	x= int(Job.Act_X+x)
	x = min(max(-fx.DISPLAY_Y,x), (fx.DISPLAY_Y-1)*2)		#Begrenzen Wert auf Matrixgröße 2x zu jeder Seite
	return int(x)
	
def TransY(Job,x,y):
	y= int(Job.Act_Y+y)
	y = min(max(-fx.DISPLAY_X,y),(fx.DISPLAY_X-1)*2)	#Begrenzen Wert auf Matrixgröße 2x zu jeder Seite
	return int(y)

def Transform(Job):
	Matrix = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=int)

	# Verschiebung in X und Y
	#print(Job.Pivot_X, Job.Pivot_Y, Job.Act_X, Job.Act_Y, Job.Act_Rotation)
	#time.sleep(0.1)

	for x in range(fx.DISPLAY_Y):
		for y in range(fx.DISPLAY_X):		#Durchlaufen der Matrixgröße und Zuweisen der transformierten Werte
			try:
				Trans_x = TransX(Job,x,y)
				Trans_y = TransY(Job,x,y)
				Center_x = Job.Pivot_X + Trans_x
				Center_y = Job.Pivot_Y + Trans_y
			except Exception as e:
				print ("Fehler in Verschiebung" + str(e.args))
				time.sleep(1)

			try:
				Radius = sqrt((Center_x-Job.Act_X) * (Center_x-Job.Act_X) + (Center_y-Job.Act_Y) * (Center_y-Job.Act_Y) )
				Winkel = atan2((Center_y-Job.Act_Y),(Center_x-Job.Act_X))/(2*pi)*360
				#Radius = sqrt((Center_x- x) * (Center_x-x) + (Center_y-y) * (Center_y-y) )
				#Winkel = atan2((Center_y-y),(Center_x-x))/(2*pi)*360
				Trans_x = int(round(cos((Winkel+Job.Act_Rotation)/360*2*pi)*Radius))#+Center_x
				Trans_y = int(round(sin((Winkel+Job.Act_Rotation)/360*2*pi)*Radius))#+Center_y
			except Exception as e:
				print ("Fehler in Rotation" + str(e.args))
				time.sleep(1)
			
			#print(x,y,round(Job.Act_X,2), round(Job.Act_Y,2),Trans_x,Trans_y,round(Radius,2),round(Winkel,2),round(Job.Act_Rotation), Job.Rotation)
			#time.sleep(1)
			if Trans_x >=0 and Trans_x <=fx.DISPLAY_Y-1 and Trans_y >= 0 and Trans_y <= fx.DISPLAY_X-1:
				try:	
					Matrix[x,y] = Job.Target_Bright[int(Trans_x),int(Trans_y)]
				except Exception as e:
					print ("Fehler in Array" + str(e.args) + ", " + str(Trans_x) + ", " + str(Trans_y))
					time.sleep(1)
			else:
				Matrix[x,y]=0

	return Matrix

#Update der LED's im separaten Thread
def UpdateLED(Speed, Jobs, Render):
	global Shadow_LED, hex_lp, Brightness_table
	staticarray = ab.static_array_from_xlsx("controller_placement.xlsx")
	RenderFrame = np.zeros((24*fx.DRIVER_COUNT),dtype=int)
	

	while len(Jobs)>0:
		Update = False		#Initialisierung des Update-Flags. Updates werden nur durchgeführt, wenn Änderungen erfolgen sollen
		for Job_Index in range(len(Jobs)):		#Alle vorhandenen Jobs durchlaufen
			try:	#Nur ausführen, wenn mindestens ein Job ansteht
				#Shadow-LED füllen, alle Jobs werden nacheinander auf Shadow-LED summiert
				try:
					Target = Transform(Jobs[Job_Index])				#Transformieren der Zielmatrix, um das Pattern zu schieben oder zu rotieren
					#print(Target)
					#time.sleep(1)
				except Exception as e:
					print ("Fehler Transform" + str(e.args) + str(Job_Index) + ", " + str(len(Jobs)))
					time.sleep(1)
				
				for x in range(Shadow_LED.shape[0]):			#Matrix füllen
					for y in range(Shadow_LED.shape[1]):
						if Jobs[Job_Index].Cycles_Elapsed > Jobs[Job_Index].Duration:		#Wenn Jobdauer überschritten ist, wird Target-Bright auf 0 gesetzt.
							Target[x,y]=0
						
						#Berechnen Actual_Bright
						if Jobs[Job_Index].Actual_Bright[x,y] < Target[x,y] and Jobs[Job_Index].Step_Bright[x,y]<=0: #Neues Ziel definiert
							#LED Step_Bright (Schrittgröße für Helligkeit definieren)
							if Jobs[Job_Index].Fade_in>0:
								Jobs[Job_Index].Step_Bright[x,y] = (Target[x,y]-Jobs[Job_Index].Actual_Bright[x,y])/Jobs[Job_Index].Fade_in
							else:
								Jobs[Job_Index].Step_Bright[x,y] = (Target[x,y]-Jobs[Job_Index].Actual_Bright[x,y])
						elif Jobs[Job_Index].Actual_Bright[x,y] > Target[x,y] and Jobs[Job_Index].Step_Bright[x,y]>=0: #Neues Ziel definiert
							#LED Step_Bright (Schrittgröße für Helligkeit definieren
							if Jobs[Job_Index].Fade_out > 0: 
								Jobs[Job_Index].Step_Bright[x,y] = -(Jobs[Job_Index].Actual_Bright[x,y]-Target[x,y])/Jobs[Job_Index].Fade_out
							else:
								Jobs[Job_Index].Step_Bright[x,y] = (Target[x,y]-Jobs[Job_Index].Actual_Bright[x,y])
						
						if Jobs[Job_Index].Step_Bright[x,y] !=0:		#Wenn Änderungen anstehen, muss ein Update erfolgen
							Update = True
							
						# Aktuelle Helligkeit berechnen
						Jobs[Job_Index].Actual_Bright[x,y] += Jobs[Job_Index].Step_Bright[x,y]
						
						#Überprüfen, ob Zielhelligkeit erreicht ist
						if Jobs[Job_Index].Step_Bright[x,y]>0:
							Jobs[Job_Index].Job_Done = False	#Zielwert noch nicht erreicht
							if Jobs[Job_Index].Actual_Bright[x,y] >= Target[x,y]:
								Jobs[Job_Index].Step_Bright[x,y]=0
								if Jobs[Job_Index].Actual_Bright[x,y]-Target[x,y]<0.1:    #für kleine Abweichungen vom Zielwert Rundungsfehler ausmerzen
									Jobs[Job_Index].Actual_Bright[x,y] = Target[x,y]
						if Jobs[Job_Index].Step_Bright[x,y]<0:
							Jobs[Job_Index].Job_Done = False	#Zielwert noch nicht erreicht
							if Jobs[Job_Index].Actual_Bright[x,y] <= Target[x,y]:
								Jobs[Job_Index].Step_Bright[x,y]=0
								if Jobs[Job_Index].Actual_Bright[x,y]-Target[x,y]>-0.1:	#für kleine Abweichungen vom Zielwert Rundungsfehler ausmerzen
									Jobs[Job_Index].Actual_Bright[x,y] = Target[x,y]
						
								
						#Actual_Brigth zu Helligkeit auf Display hinzuaddieren 
						Shadow_LED[x,y] += int(round(Jobs[Job_Index].Actual_Bright[x,y]))
						Shadow_LED[x,y]= min(Shadow_LED[x,y],63)		#Wert auf 63 begrenzen, für Look-up-Table
		
				Jobs[Job_Index].Cycles_Elapsed +=1		#Timer-Tiks für Job hochzählen
				#print("\nJob_Index :" + str(Job_Index) + " ," + str(Jobs[Job_Index].Cycles_Elapsed)+ " ," + str(Jobs[Job_Index].Next_Job_Due_In))
				#time.sleep(0.1)
				
				#Rotation und Bewegung einen Schritt weiter
				Jobs[Job_Index].Move(False)
				Jobs[Job_Index].Rotate(False)

				#print(Jobs[Job_Index].Rotation, Jobs[Job_Index].Act_X, Jobs[Job_Index].Act_Y)
				
				# Wenn der Job fertig ist, Flag setzen
				if Jobs[Job_Index].Cycles_Elapsed > Jobs[Job_Index].Duration + Jobs[Job_Index].Fade_out:	# Job ist fertig, wenn die Anzeigedauer + die Abblendzeit vorbei ist
					Jobs[Job_Index].Job_Done = True
			
			except Exception as e:
				print ("Fehler in Job" + str(e.args))
				time.sleep(1)
	
			#Ende Jobbearbeitung					
			
				#Shadow_LED an Panel senden
			for x in range(Shadow_LED.shape[0]):
				for y in range(Shadow_LED.shape[1]):
					temp =Shadow_LED[x,y]
					if temp >63:
						temp = 63
					tlc5947[staticarray[x,y]] = Brightness_table[temp] #Read Brightness value from table and write to pin taken from array
					RenderFrame[staticarray[x,y]] = Brightness_table[temp] #Write to Renderframe	
					
		#fertigen RenderFrame in Render-Matrix ablegen
		
		Render= np.append(Render,RenderFrame)
		#Schreiben & Verzögerung 
		
		if Update == True:		#Update der LED's erfolgt nur, wenn eine Änderung in der Helligkeit erfolgt
			tlc5947.write()
			time.sleep(Speed)
		
		
		#Liste aufräumen. Fertige Elemente entfernen
		Delete_list = []
		for Job_Index in range(len(Jobs)):
			if Jobs[Job_Index].Job_Done == True:
				# Element zum Löschen in Liste schreiben
				Delete_list.append(Job_Index)
				
		#Alle Elemente aus der Löschliste löschen, Rückwärts, damit die Elemente sich nicht im Index verändern
		for Item in reversed(range(len(Delete_list))):
				del Jobs[Delete_list[Item]]
		
		# Shadow_LED löschen und für nächsten Zyklus vorbereiten
		for x in range(Shadow_LED.shape[0]):			#Matrix mit 0 füllen
			for y in range(Shadow_LED.shape[1]):			#NP.Zeros verwenden
				Shadow_LED[x,y]= 0
				
	#Frame abspeichern
	
	try:
		output = open('test.rnd', 'wb')
		pickle.dump(Render, output)
		output.close()
	except Exception as e:
		print(e)
		time.sleep(1)
		
		
class Update(threading.Thread):
	def __init__(self,Speed, Jobs, Render):
		threading.Thread.__init__(self)
		self.Speed = Speed
		self.Jobs = Jobs
		self.Render = Render
		self.daemon = True
		self.start()
	
	def run(self):
		UpdateLED(self.Speed, self.Jobs, self.Render)

#Functions to apply rotation to a suiting array
def rotate_hex_by_one(array):
    if (array.shape!=(7,4)):
        return array
    new_array = np.zeros((7,4),dtype=int)
    for i in range(shift_map.size):
        np.put(new_array, i, array.flat[shift_map.flat[i]])
    array = new_array
    return array

def rotate_hex_by_n(array, n):
    for i in range(n):
        array = rotate_hex_by_one(array)
    return array

def Init_Panel():
	GPIO.setmode(GPIO.BCM) # GPIO Nummern statt Board Nummern
	GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # GPIO Modus zuweisen
	Blank_Panel(True)
	