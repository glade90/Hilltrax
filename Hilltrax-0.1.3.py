#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-4
#
"""
basic-tutorial-4: Time management
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+4%3A+Time+management
"""

import gi, sys
gi.require_version('Gst', '1.0')
from gi.repository import GObject,Gst

GObject.threads_init()
Gst.init(None)

# Python version of GST_TIME_ARGS
def convert_ns(t):
    s, ns = divmod(t, 1000000000)
    m, s = divmod(s, 60)

    if m < 60:
        return "0:%02i:%02i.%i" %(m,s,ns)
    else:
        h,m = divmod(m, 60)
        return "%i:%02i:%02i.%i" %(h,m,s,ns)

def handle_message(data, msg):
    #print("Test5")
    if msg.type == Gst.MessageType.ERROR:
        #print("Test7")
        err, debug = msg.parse_error()
        print (sys.stderr, "Error received from element %s: %s"% (message.src.get_name(), err))
        print (sys.stderr, "Debugging information: %s"% debug)
        data["terminate"] = True
    elif msg.type == Gst.MessageType.EOS:
        #print("Test8")
        print ("End-Of-Stream reached.")
        data["terminate"] = True
    elif msg.type == Gst.MessageType.DURATION_CHANGED:
        #print("Test9")
        # The duration has changed, mark the current one as invalid
        data["duration"] = Gst.CLOCK_TIME_NONE
    elif msg.type == Gst.MessageType.STATE_CHANGED:
        #print("Test10")
        #print (msg.src)
        #print (data["playbin"])
        #if msg.src == data["playbin"]:
        #print("Test11")
        old_state, new_state, pending_state = msg.parse_state_changed()
        #print (old_state)
        #print (new_state)
        #print (pending_state)
        
        print ("Pipeline state changed from %s to %s."% 
                   (Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))
        data["playing"] = (new_state == Gst.State.PLAYING)
        if data["playing"]:
            query = Gst.Query.new_seeking(Gst.Format.TIME)
            if data["playbin"].query(query):
                (aux, data["seek_enabled"], start, end) = query.parse_seeking()
                if data["seek_enabled"]:
                    print ("Seeking is ENABLED from %s to %s"%(convert_ns(start), convert_ns(end)))
                else:
                    print ("Seeking is DISABLED for this stream.")
            else:
                print("Seeking query failed.", file=sys.stderr)

    else:
        print("Unexpected message received.", file=sys.stderr)

class Main:

    def __init__(self):

        print (
            "Hilltrax - The world isn't flat\n\n"
            "USAGE: Choose one of the following options, then press enter:\n"
            " 'P' to toggle between PAUSE and PLAY\n"
            " 'S' to increase playback speed\n"
            " 'W' to slow down playback speed\n"
            " 'D' to toggle playback direction\n"
            " 'N' to move to next frame(s)  (in the current direction, better in PAUSE)\n"
            " 'Q' to quit\n");

        data = dict()

        # Create the elements
        data["playing"] = False
        data["terminate"] = False
        data["seek_enabled"] = False
        data["seek_done"] = False
        data["duration"] = Gst.CLOCK_TIME_NONE
        data["rate"] = 1.0

        # Create the elements
        data["playbin"] = Gst.ElementFactory.make("playbin", "playbin")
        data["audio_sink"] = None
        
        if (not data["playbin"]):
            print(sys.stderr, "Not all elements could be created.")
            exit(-1)

        # Set the URI to play
        #data["playbin"].set_property("uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")
        data["playbin"].set_property("uri", "file:///home/glade90/Hilltrax/TestFiles/test.mp3")
        
        # Start playing
        ret = data["playbin"].set_state(Gst.State.PLAYING)
        if ret ==  Gst.StateChangeReturn.FAILURE:
            print (sys.stderr, "Unable to set the pipeline to the playing state.")
            exit(-1)
        data["playbin"].get_state(Gst.CLOCK_TIME_NONE)
        print(data["playbin"].get_state(0))
        #print(Gst.Clock.get_time())

        # Listen to the bus
        bus = data["playbin"].get_bus()
        #print("Test")

        #while state is not ASYNC DONE
        data['playbin'].seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, 300 * Gst.SECOND)

        listener = True
        while (listener == True):
            command = str(input('Enter a command: '))
            listener = handle_keyboard(command, data) 


def handle_keyboard(keystroke,data):
        x = keystroke.lower()
        if (x == 'p'):
            data["playing"] = not data["playing"]
            data["playbin"].set_state(Gst.State.PLAYING if data.playing else Gst.State.PAUSED)
            print ("Setting state to {0}".format("PLAYING" if data.playing else "PAUSE"))
        elif (x == 's'):
            data["rate"] *= 1.1
            send_seek_event(data)
        elif (x == 'w'):
            data["rate"] /= 1.1
            send_seek_event(data)
        elif (x == 'd'):
            data["rate"] *= -1.0
            send_seek_event(data)
        elif (x == 'n'):
            if (not data.video_sink):
                #If we have not done so, obtain the sink through which we will send the step events
                data.video_sink = data.pipeline.get_property("video_sink")
            data.audio_sink.send_event(Gst.Event.new_step(Gst.Format.BUFFERS, 1, data.rate, True, False))
            print ("Stepping one frame")
        elif (x == 'q'):
            print ("Exiting Hilltrax...Enjoy your run")
            data["playbin"].set_state(Gst.State.NULL)
            return False
        return True

def send_seek_event(data):
    format = Gst.Format.TIME
    (x, position) = data["playbin"].query_position(format)
    if (not position):
        print ( sys.stderr, "Unable to retrieve current position.")
        return

    seek_event = None
    #Create the seek event
    #http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstEvent.html#gst-event-new-seek
    if (data["rate"] > 0.0):
        seek_event = Gst.Event.new_seek(data["rate"], Gst.Format.TIME, 
                        (Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE),
                        Gst.SeekType.SET, position, Gst.SeekType.SET, -1)
        print (position)
    else:
        seek_event = Gst.Event.new_seek(data["rate"], Gst.Format.TIME, 
                        (Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE),
                        Gst.SeekType.SET, 0, Gst.SeekType.SET, position)
    if (not data["audio_sink"]):
        data["audio_sink"] = data["playbin"].get_property("audio_sink")
    data["audio_sink"].send_event(seek_event)
    print ("Current rate: ", data["rate"])

start=Main()
