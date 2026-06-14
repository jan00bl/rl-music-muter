# RL Music Muter

The RL Music Muter is a small tray application for muting other applications, while goal anthems are played.  
It uses the [Rocket League Stats API](https://www.rocketleague.com/developer/stats-api)

## Usage

First enable the Rocket League Stats API by adding the following to DefaultStatsAPI.ini in your Rocket League config folder  
(default: C:/Program Files (x86)\Steam\steamapps\common\rocketleague\TAGame\Config):

```
[TAGame.MatchStatsExporter_TA]
Port=49123
PacketSendRate=1
```

> You can also use a higher PacketSendRate

Then download the latest version from the [release](https://github.com/jan00bl/rl-music-muter/releases) site.  
Put it in any folder you want and just start it.  
When it is started it shows up in the tray, where you can configure it

### Settings

All settings will be saved in the file `settings.json` which will be located in the same folder as the exe-file.

#### Processes to be muted

Here you can select the applications/processes which you want to mute, while goal anthems are played.  
Only applications that are currently running will show up here.

> Default: [Spotify.exe]

#### Mute mode

Select if the other applications should fade out/in or should get directly muted (hardcut).

> Default: Fade out/in

#### Mute entire post match

If you want that the other applications get muted during the whole post match, you can enable it here.

> Default: Disabled

## Developement

### Prerequisites

- enabled Rocket League Stats API
- python 3
- uv (a python dependency manager)

### Run

Start the RL Music Muter with the following command:

```
uv run main.py
```

### Build

Open the terminal and run

```
.\build_exe.bat
```

The exe-file will be located in the `dist`-folder
