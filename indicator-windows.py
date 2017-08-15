#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is an example for a tutorial on Ubuntu Unity/Gnome AppIndicators:
# http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html
# https://github.com/brunoseivam/todoindicator/blob/master/todo.py
# https://github.com/candidtim/vagrant-appindicator/blob/master/vgapplet/indicator.py

import signal
import time
import subprocess

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Wnck', '3.0')

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Wnck
from gi.repository import AppIndicator3 as AppIndicator


APPINDICATOR_ID = 'windows-indicator'
APPINDICATOR_ICON = 'windows-indicator'
APPINDICATOR_RATE = 1


def shell_exec(cmd):
    try:
        output = subprocess.getoutput(cmd)
    except AttributeError as _:
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = p.communicate()[0]
    return output


class IndicatorWindows(object):

    menu_item_fixed = ['Quit', 'Flat Show Windows']

    def __init__(self):
        self.init = True
        self.ind = AppIndicator.Indicator.new(APPINDICATOR_ID,
                                              APPINDICATOR_ICON,
                                              AppIndicator.IndicatorCategory.SYSTEM_SERVICES)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.build_menu()
        self.ind.set_menu(self.menu)
        GLib.timeout_add_seconds(APPINDICATOR_RATE, self.handler_timeout)
        Gtk.main_iteration()

    def main(self):
        Gtk.main()

    def handler_timeout(self):
        wids = self.get_window_wids()
        for item in self.menu.get_children():
            if item.get_label() in self.menu_item_fixed:
                continue
            if item.attrs['w'].wid not in wids or item.attrs['w'].is_active() is True:
                self.menu.remove(item)
        self.build_menu_items()
        return True

    def build_menu(self):
        self.menu = Gtk.Menu()
        self.build_menu_items()

    def build_menu_item(self, label, action, attrs=None):
        if attrs['t'] == 'image':
            mitem = Gtk.ImageMenuItem(label)
            img = Gtk.Image.new_from_pixbuf(attrs['w'].get_icon())
            mitem.set_image(img)
            mitem.set_always_show_image(True)
        else:
            mitem = Gtk.MenuItem(label)
        mitem.attrs = attrs
        mitem.connect('activate', action)
        #  attrs['direction'] == 'top' and self.menu.prepend(mitem) or self.menu.append(mitem)
        self.menu.prepend(mitem)
        attrs['direction'] == 'bottom' and self.menu.reorder_child(mitem, -1)
        mitem.show()

    def build_menu_items(self):
        wids = self.get_menu_item_wids()
        for w in self.get_windows():
            if w.wid not in wids and w.is_active() is False:
                self.build_menu_item(w.title, self.focus_window, {'direction': 'top', 't': 'image', 'w': w})
        if self.init is True:
            self.build_menu_item('Flat Show Windows', self.flat_show, {'direction': 'bottom', 't': 'label'})
            self.build_menu_item('Quit', self.quit, {'direction': 'bottom', 't': 'label'})
        self.init = False

    def flat_show(self, _):
        shell_exec('xdotool key Super_L+w')

    def quit(self, _):
        Gtk.main_quit()

    def focus_window(self, mitem):
        mitem.attrs['w'].activate(time.time())

    def get_menu_item_wids(self):
        wids = []
        for item in self.menu.get_children():
            if item.get_label() not in self.menu_item_fixed:
                wids.append(item.attrs['w'].wid)
        return wids

    def get_window_wids(self):
        return [w.wid for w in self.get_windows()]

    def get_windows(self):
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = []
        for w in screen.get_windows():
            if w.get_window_type() in [Wnck.WindowType.NORMAL, Wnck.WindowType.DIALOG]:
                wid = id(w)
                name = w.get_name()
                name = name.replace('　', ' ')
                name = name.strip()[0:50]
                icon = w.get_icon()
                wclass = w.get_class_group_name()
                title = '%s%s%s' % (name, '' if name == '' else ' - ', wclass)
                w.title, w.icon, w.wclass, w.wid = title, icon, wclass, str(wid)
                windows.append(w)
        return windows


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    indwin = IndicatorWindows()
    indwin.main()
