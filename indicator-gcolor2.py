# This code is an example for a tutorial on Ubuntu Unity/Gnome AppIndicators:
# http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html

import os
import signal
import time
import subprocess

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
# from gi.repository import Notify as notify


APPINDICATOR_ID = 'gcolor-indicator'
APPINDICATOR_ICON = 'gcolor-indicator'


def main():
    # icon = gtk.IconTheme.get_default().load_icon('gcolor2', 22, 0)
    indicator = appindicator.Indicator.new(APPINDICATOR_ID, APPINDICATOR_ICON, appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu())
    # notify.init(APPINDICATOR_ID)
    gtk.main()


def build_menu():
    menu = gtk.Menu()
    item_show = gtk.MenuItem('Show Color Picker')
    item_show.connect('activate', show)
    menu.append(item_show)

    item_hide = gtk.MenuItem('Hide It')
    item_hide.connect('activate', hide)
    menu.append(item_hide)

    item_quit = gtk.MenuItem('Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)
    menu.show_all()
    return menu


def show(_):
    # notify.Notification.new("<b>show</b>", str(output), None).show()
    p = subprocess.Popen('pidof gcolor2', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    output = p.communicate()[0]
    if output != '':
        os.system('wmctrl -a gcolor2')
    else:
        os.system('start-stop-daemon --exec /usr/bin/gcolor2 --name gcolor2 --start --background &>/dev/null')
        time.sleep(.3)

    os.system('wmctrl -a gcolor2 -e "0,500,100,0,0"')


def hide(_):
    os.system('pkill gcolor2 &>/dev/null')


def quit(_):
    # notify.uninit()
    gtk.main_quit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
