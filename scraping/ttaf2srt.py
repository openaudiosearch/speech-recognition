#!/usr/bin/env python3

"""
Usage:
ttaf2srt subtitlefilettafinput.xml > output.srt

From https://github.com/haraldF/ttaf2srt
edited for 'SWR - Pälzisch im Abgang' subtitles
www.swr.de/paelzisch-im-abgang/
and 'Tatort' subtitles.
"""
"""
From https://github.com/haraldF/ttaf2srt

ttaf2srt

Simple python script to convert ttaf subtitles to srt subtitles.
Note - only tested on German 'Tatort' subtitles.
Note2 - if using vlc or mplayer, make sure to specify 'utf8' as encoding, otherwise, special characters will not render correctly.
"""
import sys
from xml.dom import minidom

def dumpText(item):
    for child in item.childNodes:
        if child.nodeType == child.TEXT_NODE:
            print(child.nodeValue, end="")
        elif child.nodeType == child.ELEMENT_NODE:
            if child.nodeName == "br":
                print()
            elif child.nodeName == "span":
                print("<font color=\"" + styles[child.getAttribute("style")] + "\">", end="")
                dumpText(child)
                print("</font>", end="")
            elif child.nodeName == "I":
                print()
            else:
                print("Unknown Node: " + child.nodeName, file=sys.stderr)

def parse_time(timestr):
    parts = timestr.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    sec = float(parts[2])
    return ((hours * 60) + minutes) * 60 + sec

def form_time(seconds):
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600) // 60
    seconds = (seconds % 3600) % 60
    hrd = seconds - int(seconds)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d}.{int(hrd*100):02d}"

def dumpHeader(item, subCount):
    print(subCount)
    begin = item.getAttribute("begin")
    end = item.getAttribute("end")
    if end == '':
        dur = item.getAttribute("dur")
        dur_s = parse_time(dur)
        begin_s = parse_time(begin)
        end = form_time(begin_s + dur_s)
        print(f"{dur} {dur_s} {begin_s} {end}")

    # ### this is a silly hack - for some reason, my ttaf files all start at hour 10? Resetting
    # the hour makes it work again
    # begin = '0' + begin[1:]
    # end = '0' + end[1:]
    print(form_time(float(begin)) + " --> " + form_time(float(end)))

def parseStyles(styles):
    result = {}
    for style in styles:
        result[style.getAttribute('xml:id')] = style.getAttribute('tts:color')
    return result

with open(sys.argv[1]) as f:
    xmldoc = f.read() #.replace('\n', ' ').replace('\r', '')
xmldoc = minidom.parseString(xmldoc)

header = xmldoc.getElementsByTagName('head')
if len(header):
    styling = header[0].getElementsByTagName('styling')
    if len(styling):
        styles = parseStyles(styling[0].getElementsByTagName('style'))

body = xmldoc.getElementsByTagName('body')

itemlist = body[0].getElementsByTagName('p') 

subCount = 0

for item in itemlist:
    # if item.hasAttribute('xml:id'):
    dumpHeader(item, subCount)
    subCount += 1
    # if item.hasAttribute('style'):
    #     color = styles[item.getAttribute("style")]
    # if color:
    #     print("<font color=\"" + color + "\">", end="")
    dumpText(item)
    # if color:
    #     print("</font>", end="")
    print("\n")
