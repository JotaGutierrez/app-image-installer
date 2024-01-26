# App Image Installer
Very simple script to ease installing app images or other self-contained executables.

## Installation
* Just download appImageInstaller.py,
* make it executable and
* move it, or symlink, to some place in $PATH (ie: /usr/local/bin)

## Usage
The script works by moving the appImage (or any other script or executable) to /opt and creating a symlink in /usr/local/bin.
It allows to take track of installed apps, uninstall without losing the file and create a Gnome launcher. 


Let's imagine you have arduino-ide_2.2.1_Linux_64bit.AppImage in ~/Downloads. 

To install it:
```shell
$ appImageInstaller.py ~/Downloads/arduino-ide_2.2.1_Linux_64bit.AppImage Arduino
```
This will make arduino executable from terminal as 
```shell
$ Arduino
```

If you use Gnone, you can also create a launcher:
```shell
$ appImageInstaller.py launcher Arduino
```

You can get a list of installed apps and some extra info:
```shell
$ appImageInstaller.py list
```

Finally, to uninstall the app:
```shell
$ appImageInstaller.py uninstall Arduino
```
