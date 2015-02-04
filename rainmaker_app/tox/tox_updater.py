#!/usr/bin/env python3
#https://raw.githubusercontent.com/Jman012/Tox-DHTNodes-Updater/master/DHTNodes_updater.py
from __future__ import print_function

import urllib
import sys
import os
import time
import threading

import tox_env

def spin(stop=threading.Event):
    if stop is None:
        return

    print("|", end="")
    while True:
        for c in "/-\\|":
            if stop.is_set():
                return

            sys.stdout.write("\b{}".format(c))
            sys.stdout.flush()
            time.sleep(0.1)

def download():
    print("Downloading")
    stop = threading.Event()
    spinner = threading.Thread(target=spin, args=(stop,))
    spinner.start()

    try:
        request = urllib.urlopen(tox_env.NODES_URL)
        raw_page = request.read().decode("utf-8")
    except:
        print("Couldn't download")
        stop.set()
        return
    
    stop.set()
    sys.stdout.write("\b")
    sys.stdout.flush()

    return raw_page

def fetch(raw_page=None):
    if raw_page is None:
        raw_page = download()

    print("Parsing")

    # Get rid of everything around the table
    raw_table = raw_page[raw_page.find("<table"):raw_page.find("</table")]
    del raw_page

    # Get rid of the `<table border="0" cell...>`,
    # and the `</table>` is already gone
    raw_table = raw_table[raw_table.find("\n"):]

    # Get rid of the header
    raw_table = raw_table[raw_table.find("<tr "):]

    # Separate each section into a list
    node_list = []
    count = raw_table.count("<tr ")
    for i in range(count):
        ipv4 = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        ipv6 = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        port = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        key = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        name = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        location = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td>\n<td>")+5:]
        status = raw_table[raw_table.find("<td>") + 4:raw_table.find("</td>") - 1]
        raw_table = raw_table[raw_table.find("</td></tr>")+5:]

        # print(ipv4, ipv6, port, key, name, location, status)
        node_list.append((ipv4, int(port), key))
    print("Success")
    return node_list
