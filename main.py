# Import socket module 
import socket             
from pycaw.pycaw import AudioUtilities
import time
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image
import json
from threading import Thread, current_thread, Timer, Lock
import comtypes
import os
import sys

class MuteState:
    MUTED = 1
    MUTING = 2
    UNMUTED = 3
    UNMUTING = 4

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_volume(process):
    for session in AudioUtilities.GetAllSessions():
        volume = session.SimpleAudioVolume
        if session.Process and session.Process.name() == process:
            return volume

def mute(muteProcess, process):
    with mutedProcessesLock:
        if not process in mutedProcesses.keys():
            mutedProcesses[process] = MuteState.UNMUTED
        if muteProcess and (mutedProcesses[process] == MuteState.MUTED or mutedProcesses[process] == MuteState.MUTING):
            return
        if not muteProcess and (mutedProcesses[process] == MuteState.UNMUTED or mutedProcesses[process] == MuteState.UNMUTING):
            return
    
        prevMuteState = mutedProcesses[process]

        if muteProcess:
            mutedProcesses[process] = MuteState.MUTING
        else:
            mutedProcesses[process] = MuteState.UNMUTING

        volume = get_volume(process)

        if settings["muteMode"] == "hardcut":
            volume.SetMute(muteProcess, None)
            if muteProcess:
                mutedProcesses[process] = MuteState.MUTED
            else:
                muteProcess[process] = MuteState.UNMUTED
            return

        if muteProcess:
            if prevMuteState == MuteState.UNMUTED:
                processVolumes[process] = volume.GetMasterVolume()
            muteThread = Thread(target = fade_out, args=[process,volume,0.5])
            muteThread.start()
        else:
            volumeGoal = processVolumes[process]
            muteThread = Thread(target = fade_in, args=[process,volume,0.5,volumeGoal])
            muteThread.start()


def fade_out(process, volume, duration):
    currentVolume = volume.GetMasterVolume()
    timeStep = duration / 100
    volumeStep = currentVolume / 100
    while currentVolume > 0 and mutedProcesses[process] == MuteState.MUTING:
        currentVolume = max(0, currentVolume - volumeStep)
        volume.SetMasterVolume(currentVolume, None)
        time.sleep(timeStep)
    with mutedProcessesLock:
        if mutedProcesses[process]  == MuteState.MUTING:
            processVolumes[process] = MuteState.MUTED


def fade_in(process, volume, duration, volumeGoal):
    currentVolume = volume.GetMasterVolume()
    timeStep = duration / 100
    volumeStep = volumeGoal / 100
    while currentVolume < volumeGoal and mutedProcesses[process]  == MuteState.UNMUTING:
        currentVolume = min(volumeGoal, currentVolume + volumeStep)
        volume.SetMasterVolume(currentVolume, None)
        time.sleep(timeStep)
    with mutedProcessesLock:
        if mutedProcesses[process]  == MuteState.UNMUTING:
            processVolumes[process] = MuteState.UNMUTED


def mute_all(isMuted):
    for process in settings["processesToMute"] :
        mute(isMuted, process)

def processEvents(event):
    if event.find("GoalReplayStart") != -1 or event.find("MatchEnded") != -1:
        print("GoalReplayStart | MatchEnded")
        mute_all(True)
    elif event.find("GoalReplayEnd") != -1 or event.find("MatchDestroyed") != -1 or event.find("PodiumEnd") != -1:
        print("GoalReplayEnd | MatchDestroyed | PodiumEnd")
        mute_all(False)

def set_setting(setting,value):
    if setting == "muteEntirePostMatch":
        settings["muteEntirePostMatch"] = value
    elif setting == "processesToMute":
        if value in settings["processesToMute"]:
            settings["processesToMute"].remove(value)
        else:
            settings["processesToMute"].append(value)
    elif setting == "muteMode":
        settings["muteMode"] = value
    
    with open(saveFile, 'w') as f:
        json.dump(settings, f)

def test_mute():
    global testMute
    testMute = not testMute
    if testMute:
        mute_all(True)
    else:
        mute_all(False)

def closeApp():
    global running
    running = False

def create_process_menu_item(processName):
    return item(
                    processName,
                    lambda _: set_setting("processesToMute", processName),
                    lambda _: processName in settings["processesToMute"]
                )

def updateTray():
    comtypes.CoInitialize()
    ic = Image.open(resource_path("Icon.ico"))
    tray = icon("RL Music Muter", icon=ic, title="RL Music Muter")
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
                if(session.Process == None):
                    continue
                menuItems.append(create_process_menu_item(session.Process.name()))

            tray.menu = menu(item(
                'Processes to be muted',
                menu(*menuItems)
            ),
            item(
                'Mute mode',
                menu(
                    item(
                        'Fade Out/In',
                        lambda _: set_setting("muteMode", "fadeOut"),
                        checked=lambda _: settings["muteMode"] == "fadeOut"
                    ),
                    item(
                        'Hardcut',
                        lambda _: set_setting("muteMode", "hardcut"),
                        checked=lambda _: settings["muteMode"] == "hardcut"
                    )
                )
            ),
            item(
                'Mute entire post match',
                lambda _: set_setting("muteEntirePostMatch", not settings["muteEntirePostMatch"]),
                checked=lambda _: settings["muteEntirePostMatch"]
            ),
            item(
                'Test mute',
                test_mute,
                checked=lambda _: testMute
            ),
            item(
                'Close',
                closeApp
            ))
        time.sleep(2)
            
    tray.stop()

# Create a socket object
s = socket.socket()
s.settimeout(2)
mutedProcesses = {}
mutedProcessesLock = Lock()
processVolumes = {}
isConnected = False
settings = {"processesToMute": ["Spotify.exe"], "muteEntirePostMatch" : False, "muteMode": "fadeOut"}
running = True
saveFile= 'settings.json'
sessions = []
testMute = False

# Define the port on which you want to connect
port = 49123

try:
    with open(saveFile, "r") as file:
        d = json.load(file)
        if type(d) == dict:
            settings = d
except:
    print("could not load settings, use default settings")
    with open(saveFile, "w") as writeFile:
        json.dump(settings, writeFile)


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