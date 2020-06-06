#encoding: utf-8
# first do this: https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
# sudo pip3 install adafruit-circuitpython-tlc5947
# sudo apt-get install python3-pandas
# pip3 install xlrd --user
# Using GIT-Server with Raspberry:
# git status : Display actual status
# git add "Filename" add file to version log
# git commit -m "Comment" Commit version log including Comment
# git push -> finally commit version to GIT-server, using username and password

import os
import time
import curses
import numpy as np
import LED
import pandas as pd
import fixedsizes as fx
import pickle
import lirc

# Array zum Speichern der Positionen innerhalb eines Jobs
Job_Matrix = np.zeros((fx.DISPLAY_Y,fx.DISPLAY_X),dtype=int)
#erzeuge Liste mit Jobs, zunächst das erste Element
Jobs = [LED.JOB()]
Jobs_Pending = []


#Jobs = []

Brightness = 10

def Get_Pattern(Job_List):
    #Lese Pattern aus Excel-File
    #   0:Job_Number
    #   1:Activity
    #   2:Duration
    #   3:Next_Job_Due_In
    #   4:Fade_in
    #   5:Fade_out
    #   6:Overwrite behavior
    #   7:StartX
    #   8:StartY
    #   9:Move X
    #   10:Move Y
    #   11:Rotate
    #   12:PivotX
    #   13:PivotY
    #   Ab 14: Matrix
    
    while len(Job_List)>0:
        Job_List.pop()
    
    Array = np.array(pd.read_excel('Pattern.xlsm', sheet_name = "Program 0"))
    try:
        for i in range(Array.shape[0]):
            #alle Zeilen der Liste einlesen
            Job = LED.JOB()    #Neues Objekt für die Zeile anlegen
            Job.Number= Array[i,0]
            Job.Activity= Array[i,1]
            Job.Duration = Array[i,2]
            Job.Next_Job_Due_In = Array[i,3]
            Job.Fade_in = Array[i,4]
            Job.Fade_out = Array[i,5]
            Job.Overwrite_Behavior = Array[i,6]
            Job.Start_X = Array[i,7]
            Job.Start_Y = Array[i,8]
            Job.Move_X = Array[i,9]
            Job.Move_Y = Array[i,10]
            Job.Rotation = Array[i,11]
            Job.Pivot_X= Array[i,12]
            Job.Pivot_Y= Array[i,13]
            Job.Target_Bright = Array[i,14:]
            Job.Target_Bright= np.reshape(Job.Target_Bright, (fx.DISPLAY_Y,fx.DISPLAY_X))
            Job.Rotate(True) # Startpunkt für Rotation definieren
            Job.Move(True) # Startpunkt für Bewegung definieren
            Job_List.append(Job)
    except Exception as e:
        print("\nExcel-Routine :"+ str(e.args))
        time.sleep(1)
    return Array.shape[0]    

def main(win):
    global Brightness, Job_Matrix, Jobs, Render

    Brightness = 100
     #initialisieren GPIO's und LED's
    LED.Init_Panel()
    win.nodelay(False)
    key=""
    win.clear()
    win.addstr("Detected key:")
    try:
        while 1:
            time.sleep(0.05)
            try:
                key = win.getkey()
                win.clear()
                win.addstr("To exit, use ENTER\n")
                win.addstr("Detected key:")
                win.addstr(str(key))
                win.addstr(":")
                if key == os.linesep:
                    LED.Blank_Panel(False)
                    break
                elif (str(key) == "t"):
                    LED.Blank_Panel(False)
                    win.addstr("\nTest Panel")
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = 1023  #Alle lampen an
                    LED.tlc5947.write()
                    time.sleep(1)

                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = 0  #Alle lampen aus
                    LED.tlc5947.write()
                    time.sleep(1)

                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = (i%2)*100  #Grade lampen an
                    LED.tlc5947.write()
                    time.sleep(1)

                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = ((i+1)%2)*100  #Ungrade lampen an
                    LED.tlc5947.write()
                    time.sleep(1)

                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = int(Brightness)  #alle lampen an
                    LED.tlc5947.write()
                    time.sleep(1)

                elif (str(key) == "b"):
                    LED.Blank_Panel(False)
                    win.addstr("\nToggle blank")
                    LED.Blank_Panel(True)
                    time.sleep(1)
                    LED.Blank_Panel(False)
                    
                elif (str(key) == "s"):
                    LED.Blank_Panel(False)
                    win.addstr("\nTest Sequence")
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = 64  #Alle lampen an
                        LED.tlc5947.write()
                        time.sleep(0.05)
                        LED.tlc5947[i] = 8
                
                elif (str(key) == "c"):
                    win.addstr("\nTest Sequence")
                    
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = 0  #Alle lampen aus
                    LED.tlc5947.write()
                    for j in range(0,500):      #100 mal wiederholen     
                        for i in range(0,LED.DRIVER_COUNT):
                            LED.tlc5947[i*24] =64  # Segment 0 auf allen Treibern an
                        LED.tlc5947.write()
                        time.sleep(0.1)

                elif (str(key) == "f"):
                    win.addstr("\nTest Sequence")
                    LED.Blank_Panel(False)
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = 0  #Alle lampen aus
                    LED.tlc5947.write()
                    for j in range(0,500):      #100 mal wiederholen     
                        for Hell in range(0,63):
                            for i in range(0,880):
                                LED.tlc5947[i]=LED.Brightness_table[int(Hell)]
                            LED.tlc5947.write()


                elif (str(key) == "+"):
                    LED.Blank_Panel(False)
                    Brightness = (Brightness*1.05)
                    Brightness = min(Brightness,4095)
                    win.addstr("\nBrightness: " + str(Brightness))
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = int(Brightness)  #Alle lampen an
                    LED.tlc5947.write()

                elif (str(key) == "-"):
                    LED.Blank_Panel(False)
                    Brightness = (Brightness/1.05)
                    Brightness = max(Brightness,1)
                    win.addstr("\nBrightness: " + str(Brightness))
                    for i in range(0,24*LED.DRIVER_COUNT):
                        LED.tlc5947[i] = int(Brightness)  #Alle lampen an
                    LED.tlc5947.write()
 
                    
                elif (str(key) == "a"):
                    LED.Blank_Panel(False)
                    win.addstr("\nAdressing Shadow")
                    # Bestehende Jobliste löschen
                    while len(Jobs)>0:
                        Jobs.pop()
                    # Liste mit Pending Jobs laden
                    try:
                        FileAge = os.path.getmtime("Pattern.xlsm")
                    except Exception as e:
                        pass
                    Count = Get_Pattern(Jobs_Pending)       # Lädt die Jobs aus dem Excel file in eine Warteliste, gibt die Anzahl der geladenen Jobs zurück
                    Next_Job_Index = 0      #Zeiger auf den nächsten Job 
                    #Hauptschleife zum Einfügen der Pending-Jobs in die aktive Jobliste
                    Jobs.append(Jobs_Pending[Next_Job_Index])    # ersten Job laden

                    # Starten Hintergrund-Rendering
                    try:
                        Render = np.zeros(960,dtype=int)
                        t1 = LED.Update(0.1, Jobs, Render)
                    except Exception as e:
                        win.addstr("\nFehler Start T1: ")
                        win.addstr(str(e.args))    
                    
                    Next_Job_Index += 1
                    try:
                        while Next_Job_Index < Count:        # alle weiteren Jobs laden, solange noch welche da sind
                            while Jobs[-1].Next_Job_Due_In > Jobs[-1].Cycles_Elapsed:       # Neuen Job dann laden, wenn der Job davor es anzeigt
                                time.sleep(0.1)
                            Jobs.append(Jobs_Pending[Next_Job_Index])    # nächsten Job laden
                            Next_Job_Index += 1
                            #print("\nNeuer Job geladen: " + str(Next_Job_Index) + ", " + str(len(Jobs)))
                    except Exception as e:
                        win.addstr("\nFehler Jobzuordnung: ")
                        win.addstr(str(e.args))    
                    while len(Jobs)>0:              #Warten, bis HIntergrundroutine alle Jobs erledigt und aus Liste gelöscht hat
                        try:
                            if FileAge != os.path.getmtime("Pattern.xlsm"):
                                break
                        except Exception as e:
                            break                       
                    # Fertig.
                    

                elif (str(key) == "r"):     #Wiedergeben gerenderter Frames
                    LED.Blank_Panel(False)
                    win.addstr("\nShow Frames")
                    Render = 0
                    f=open('test.rnd','rb')
                    Render = pickle.load(f)
                    f.close
                    Form = np.shape(Render)
                    Render.shape = (int(Form[0]/960),960)
                    Form = np.shape(Render)
                    LengthFrame = Form[1]
                    NumberFrames =Form[0]
                    for FrameCount in range(0,NumberFrames):
                        #Frame = Render[FrameCount]
                        for FrameAdress in range(0,LengthFrame):
                            LED.tlc5947[FrameAdress]=Render[FrameCount,FrameAdress]
                        LED.tlc5947.write()
                        
            except Exception as e:
                win.addstr("\nFehler innen")
                win.addstr(str(e.args))
               # No input
    except Exception as e:
        win.addstr("\nFehler aussen")
        win.addstr(str(e.args))

def led_menu():
    selected_panel = 0

curses.wrapper(main)

sockid=lirc.init("appleremote", blocking = False)
while True:
    codeIR = lirc.nextcode()
    if codeIR != []:
        if codeIR[0] == "KEY_UP":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_DOWN":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_LEFT":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_RIGHT":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_OK":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_MENU":
            print(str(codeIR[0]))
        elif codeIR[0] == "KEY_PLAYPAUSE":
            print(str(codeIR[0]))
    time.sleep(0.05)                

#EOF
