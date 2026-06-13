# Import socket module 
import socket             
from pycaw.pycaw import AudioUtilities
import time
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw
import json
from threading import Thread, current_thread, Timer
import comtypes
import os
import sys
from functools import partial

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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
    if event.find("GoalReplayStart") != -1 or event.find("MatchEnded") != -1:
        for programm in settings["programmsToMute"] :
            mute(1, programm)
    elif event.find("GoalReplayEnd") != -1 or event.find("MatchDestroyed") != -1 or event.find("PodiumEnd") != -1:
        for programm in settings["programmsToMute"] :
            mute(0, programm)

def set_setting(setting,_,item):
    if setting == "muteEntirePostMatch":
        settings["muteEntirePostMatch"] = not settings["muteEntirePostMatch"]
    elif setting == "programmsToMute":
        if item.text in settings["programmsToMute"]:
            settings["programmsToMute"].remove(item.text)
        else:
            settings["programmsToMute"].append(item.text)
    
    with open(saveFile, 'w') as f:
        json.dump(settings, f)

def closeApp():
    global running
    running = False

def updateTray():
    comtypes.CoInitialize()
    ic = Image.open(resource_path("Icon.ico"))
    tray = icon('RL Music Muter', icon=ic)
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
                    partial(set_setting, "programmsToMute"),
                    lambda item: item.text in settings["programmsToMute"]
                ))

            tray.menu = menu(item(
                'Programms to be muted',
                menu(*menuItems)
            ),
            item(
                'Mute entire post match',
                partial(set_setting, "muteEntirePostMatch"),
                checked=lambda item: settings["muteEntirePostMatch"]
            ),
            item(
                'Close',
                closeApp
            ))
            
    tray.stop()

# Create a socket object
s = socket.socket()
s.settimeout(2)
mutedProgramms = {}
isConnected = False
settings = {"programmsToMute": ["Spotify.exe"], "muteEntirePostMatch" : False}
running = True
saveFile= 'settings.json'
sessions = []

# Define the port on which you want to connect
port = 49123



with open(saveFile, "w+") as f:
    try:
        d = json.load(f)
        if type(d) in (dict):
            settings = d
    except:
        json.dump(settings, f)


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
            time.sleep(2)
            continue
    
    try:
        event = s.recv(4096).decode()
        processEvents(event)
        if(not settings["muteEntirePostMatch"] and event.find("PodiumStart") != -1):
            timer = Timer(5, processEvents, ["PodiumEnd"])
            timer.start()
    except socket.timeout:
        None
    except ConnectionResetError:
        isConnected = False
        print("connection lost")


# close the connection
t.do_run = False
s.close()