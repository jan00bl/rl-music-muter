# Import socket module 
import socket             
from pycaw.pycaw import AudioUtilities
import time
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw
import json
from threading import Thread, current_thread
import comtypes

def create_image(width, height, color1, color2):
    # Generate an image and draw a pattern
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)

    return image

def mute(isMuted, process):
    if process in mutedProgramms.keys() and mutedProgramms[process] == isMuted:
        return
    
    mutedProgramms[process] = isMuted

    for session in AudioUtilities.GetAllSessions():
        volume = session.SimpleAudioVolume
        if session.Process and session.Process.name() == process:
            volume.SetMute(isMuted, None)

def processEvents(event):
    if event.find("ReplayPlaybackStart") != -1 or event.find("MatchEnded") != -1:
        for programm in programmsToMute :
            mute(1, programm)
    elif event.find("ReplayPlaybackEnd") != -1 or event.find("MatchDestroyed") != -1:
        for programm in programmsToMute :
            mute(0, programm)

def on_click(_,item):
    if item.text in programmsToMute:
        programmsToMute.remove(item.text)
    else:
        programmsToMute.append(item.text)

    with open(saveFile, 'w') as f:
        json.dump(programmsToMute, f)

def closeApp():
    global running
    running = False

def updateTray():
    comtypes.CoInitialize()
    tray = icon('test name', icon=create_image(64, 64, 'magenta', 'black'))
    tray.run_detached()
    sessions = []
    t = current_thread()
    while getattr(t, "do_run", True):
        menuItems = []
        newSessions = AudioUtilities.GetAllSessions()
        oldSessionNames = list(map(lambda x: x.Process.name() if x.Process else None, sessions))
        refreshTray = False

        if(len(sessions) != len(newSessions)):
            refreshTray = True
            sessions = newSessions


        for session in newSessions:
            if(refreshTray):
                break
            if(not session.Process):
                continue

            if(session.Process.name() not in oldSessionNames):
                sessions = newSessions
                refreshTray = True
                break

            

        if(refreshTray):
            print("refreshing tray")

            for session in sessions:
                if(not session.Process):
                    continue

                menuItems.append(item(
                    session.Process.name(),
                    on_click,
                    lambda item: item.text in programmsToMute
                ))

            tray.menu = menu(item(
                'Programms to be muted',
                menu(*menuItems)
            ),
            item(
                'Close',
                closeApp
            ))
            
    tray.stop()

# Create a socket object
s = socket.socket()
mutedProgramms = {}
isConnected = False
programmsToMute= ["Spotify.exe"]
running = True
saveFile= 'mutedProgramms.json'
sessions = []

# Define the port on which you want to connect
port = 49123



with open(saveFile, "w+") as f:
    try:
        d = json.load(f)
        if type(d) in (tuple, list):
            programmsToMute = d
    except:
        json.dump(programmsToMute, f)


t = Thread(target = updateTray)
t.start()

while running:

    # receive data from the server and decoding to get the string.
    if not isConnected:
        try:
            s.connect(('127.0.0.1', port))
            isConnected = True
            print("connected")
        except:
            print("cant connect")
            time.sleep(5)
            continue
    
    try:
        event = s.recv(4096).decode()
        processEvents(event)
    except ConnectionResetError:
        isConnected = False
        print("connection lost")


# close the connection
t.do_run = False
s.close()