#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2014 Sean Davis <smd.seandavis@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3, as published
#   by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re

from gi.repository import GLib

import logging
logger = logging.getLogger('menulibre')


def enum(**enums):
    """Add enumarations to Python."""
    return type('Enum', (), enums)

MenuItemTypes = enum(
    SEPARATOR=-1,
    APPLICATION=0,
    LINK=1,
    DIRECTORY=2
)


def getDefaultMenuPrefix():
    """Return the default menu prefix."""
    prefix = os.environ.get('XDG_MENU_PREFIX', '')

    # Cinnamon doesn't set this variable
    if prefix == "":
        if 'cinnamon' in os.environ.get('DESKTOP_SESSION', ''):
            prefix = 'cinnamon-'

    if len(prefix) == 0:
        logger.warning("No menu prefix found, MenuLibre will not function "
                        "properly.")

    return prefix


def getItemPath(file_id):
    """Return the path to the system-installed .desktop file."""
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'applications', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserItemPath():
    """Return the path to the user applications directory."""
    item_dir = os.path.join(GLib.get_user_data_dir(), 'applications')
    if not os.path.isdir(item_dir):
        os.makedirs(item_dir)
    return item_dir


def getDirectoryPath(file_id):
    """Return the path to the system-installed .directory file."""
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'desktop-directories', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserDirectoryPath():
    """Return the path to the user desktop-directories directory."""
    menu_dir = os.path.join(GLib.get_user_data_dir(), 'desktop-directories')
    if not os.path.isdir(menu_dir):
        os.makedirs(menu_dir)
    return menu_dir


def getUserMenuPath():
    """Return the path to the user menus directory."""
    menu_dir = os.path.join(GLib.get_user_config_dir(), 'menus')
    if not os.path.isdir(menu_dir):
        os.makedirs(menu_dir)
    return menu_dir


def getSystemMenuPath(file_id):
    """Return the path to the system-installed menu file."""
    for path in GLib.get_system_config_dirs():
        file_path = os.path.join(path, 'menus', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getDirectoryName(directory_str):
    """Return the directory name to be used in the XML file."""
    # Get the menu prefix
    prefix = getDefaultMenuPrefix()

    basename = os.path.basename(directory_str)
    name, ext = os.path.splitext(basename)

    # Handle directories like xfce-development
    if name.startswith(prefix):
        name = name[len(prefix):]
        name = name.title()

    # Handle X-GNOME, X-XFCE
    if name.startswith("X-"):
        # Handle X-GNOME, X-XFCE
        condensed = name.split('-', 2)[-1]
        non_camel = re.sub('(?!^)([A-Z]+)', r' \1', condensed)
        return non_camel

    # Cleanup ArcadeGames and others as per the norm.
    if name.endswith('Games') and name != 'Games':
        condensed = name[:-5]
        non_camel = re.sub('(?!^)([A-Z]+)', r' \1', condensed)
        return non_camel

    # GNOME...
    if name == 'AudioVideo' or name == 'Audio-Video':
        return 'Multimedia'

    if name == 'Game':
        return 'Games'

    if name == 'Network' and prefix != 'xfce-':
        return 'Internet'

    if name == 'Utility':
        return 'Accessories'

    if name == 'System-Tools':
        if prefix == 'lxde-':
            return 'Administration'
        else:
            return 'System'

    if name == 'Settings':
        if prefix == 'lxde-':
            return 'DesktopSettings'
        else:
            return 'Preferences'

    if name == 'Settings-System':
        return 'Administration'

    if name == 'GnomeScience':
        return 'Science'

    if name == 'Utility-Accessibility':
        return 'Universal Access'

    # We tried, just return the name.
    return name


def getRequiredCategories(directory):
    """Return the list of required categories for a directory string."""
    prefix = getDefaultMenuPrefix()
    if directory is not None:
        basename = os.path.basename(directory)
        name, ext = os.path.splitext(basename)

        # Handle directories like xfce-development
        if name.startswith(prefix):
            name = name[len(prefix):]
            name = name.title()

        if name == 'Accessories':
            return ['Utility']

        if name == 'Games':
            return ['Game']

        if name == 'Multimedia':
            return ['AudioVideo']

        else:
            return [name]
    else:
        # Get The Toplevel item if necessary...
        if prefix == 'xfce-':
            return ['X-XFCE', 'X-Xfce-Toplevel']
    return []


def getSaveFilename(name, filename, item_type):
    """Determime the filename to be used to store the launcher.

    Return the filename to be used."""
    # Check if the filename is writeable. If not, generate a new one.
    if filename is None or len(filename) == 0 or \
            not os.access(filename, os.W_OK):
        # No filename, make one from the launcher name.
        if filename is None or len(filename) == 0:
            basename = name.lower().replace(' ', '-')

        # Use the current filename as a base.
        else:
            basename = os.path.basename(filename)

        # Split the basename into filename and extension.
        name, ext = os.path.splitext(basename)

        # Get the save location of the launcher base on type.
        if item_type == 'Application':
            path = getUserItemPath()
            ext = '.desktop'
        elif item_type == 'Directory':
            path = getUserDirectoryPath()
            ext = '.directory'

        # Create the new base filename.
        filename = os.path.join(path, name)
        filename = "%s%s" % (filename, ext)

        # Append numbers as necessary to make the filename unique.
        count = 1
        while os.path.exists(filename):
            new_basename = "%s%i%s" % (name, count, ext)
            filename = os.path.join(path, new_basename)
            count += 1

    return filename