import cv2
import sys
import numpy as np
import math
from opencvpipe import GripPipeline
from networktables import NetworkTables
import time
import datetime
import threading
import copy
import logging

#*********************************************************************************
# MooseVision 2017
# Team 1391 Vision Processing Software
#
# Processes images from two separate cameras (one for each target type) using OpenCV libraries and a processing pipeline created in GRIP (found in opencvpipe.py: must exist in same directory).
# Communicates distance and angle values to the roboRIO via the National Instruments NetworkTables format using the pynetworktables module.
# Outputs diagnostic information to the terminal; can be piped to a text file using crontab.
#
#*********************************************************************************


hfov = 47
vpixel = 480
halfvpixel = 240
hpixel = 640
halfhpixel = 320
boilertargetheight = 85.02
boilercamangle = 45
geartargetheight = 5

class MultiThreadVariable:

    def __init__(self, value):
        self.value = value
        self.Lock = threading.Lock()

    def write(self, value):
        with self.Lock:
            self.value = copy.copy(value)

    def read(self):
        with self.Lock:
            return self.value


def getBoilerDist(w1, h1, y1, function):
    #if function == 0:
    #17.625 is arbitrary, but it worked
    relangle = boilercamangle - 17.625*(float((h1+y1)-halfvpixel)/halfvpixel)
    #print 'relangle: '+ str(relangle)
    dist = (boilertargetheight/math.tan(math.radians(relangle)))
        #print 'dist: '+str(dist)
    return dist

#Determines angle to the boiler
def getBoilerAngle(centerx):
    return  hfov*(float(halfhpixel-centerx)/halfhpixel)

#Determines whether x or y values are within a given margin of each other ***currently unused***
def valComparator(input1, input2, margin):
    if abs(input1 - input2) <= margin:
        return True
    else:
        return False

#Determines angle between robot heading and gear post
def getGearAngle(centerx):
    return  hfov*(float(halfhpixel-centerx)/halfhpixel)

#Determines distance from camera to gear post
def getGearDist(h):
    #16.5 is arbitrary, but it worked
    return (geartargetheight*vpixel)/(2*h*(math.tan(math.radians(16.5))))

#Fancier way of getting angle to gear post
#def getGearAngleComplex(dist, angle, x1, x2, w1, w2):
    #if x1 > x2:
        #targright = x1 + w1
        #targleft = x2

    #else:
        #targright = x2 + w2
        #targleft = x1
    #targwidth = targleft - targright
    #exptargetw = dist*math.tan(radians(angle))
    #smallangle = hfov*(float(halfhpixel-targetleft)/halfhpixel)
    #try:

#finds relevent info for contours
def contourReport(contour):
    x, y, w, h = cv2.boundingRect(contour)
    centerx = x + (w/2)
    centery = y + (h/2)
    aspect = float(w)/h
    return x, y, w, h, centerx, centery, aspect


#Opens a connection with IP Camera at a given ip, ip passed as a string

#function attempts to connect a number of times given by numTries
def connectCamera(addr, camera, numTries):
    for x in range(0, numTries):
        #outputs diagnostics info to SmartDashboard and /home/metalmoose/logs/cronlog in rpi when crontab is configured
        statusName = camera+'CamStatus'
        logging.info("Connecting to "+camera+"Cam")
        if isNetworked:
            sd.putString(statusName, 'Connecting...')

        #handles exeptions caused by no available camera; prevents program crash
        try:
            ipcam = cv2.VideoCapture(addr)
        except:
            logging.warning('Failed to connect to '+camera+'Cam!')
            if isNetworked:
                sd.putString(statusName, "DISCONNECTED")
            camStatus = 0
            continue

        #Pulls test frame to test camera connection
        camTestBool, val = ipcam.read()

        if camTestBool == False:
            logging.warning('Failed to connect to '+camera+'Cam!')
            if isNetworked:
                sd.putString(statusName, "DISCONNECTED")
            camStatus = 0
            continue

        else:
            camStatus = 1

        if camStatus == 1:
            logging.info('Connected to '+camera+'Cam')
            if isNetworked:
                sd.putString(statusName, 'Connected')
            return ipcam
    return False

# Buggy, do not use
def sdPut(type, name, value):
    if (isNetworked == True):
        try:
            if (self.type == 'number'):
                sd.putNumber(self.name, self.value)
            if (self.type == 'string'):
                sd.putString(self.name, self.value)
            if (self.type == 'boolean'):
                sd.putBoolean(self.name, self.value)
        except:
            print name + str(value)

def manageProcessing():
    global pipe
    global sharedImageTuple
    global isNewFrame
    global isDebugging
    logging.info('Computation thread initialized')
    while True:
        if (isNewFrame.read() == False):
            logging.debug('New frame not ready; no process attempted')
            continue
        else:
            logging.info('Reading frame from cameraManager...')
            img, visionState = sharedImageTuple.read()
            logging.info('Done')
            logging.info('Processing image for contours...')
            outputs, hsl = pipe.process(img)
            logging.info('Done')
            #orders contours by area in list
            contours = sorted(outputs, key=cv2.contourArea, reverse=True)
            #print 'Contours processed'

            #Finds relevant info from two largest contours, if and only if there are two or more
            if len(contours) >= 2:
                logging.info('Processing contour attributes...')
                x1, y1, w1, h1, centerx1, centery1, aspect1 = contourReport(contours[0])
                x2, y2, w2, h2, centerx2, centery2, aspect2 = contourReport(contours[1])
                logging.info('Done.')

                #draws bounding rectangles for visual debugging
                if isDebugging:
                    cv2.rectangle(img, (x1,y1), (x1+w1, y1+h1), (255,0,0), 1) #for laptop debugging ONLY
                    cv2.rectangle(img, (centerx1, centery1), (centerx1, centery1), (0,0,255), 1) #for laptop debugging ONLY
                    cv2.rectangle(img, (x2,y2), (x2+w2, y2+h2), (255,0,0), 1) #for laptop debugging ONLY
                    cv2.rectangle(img, (centerx2, centery2), (centerx2, centery2), (0,0,255), 1) #for laptop debugging ONLY
                    cv2.rectangle(img, (320, 240), (320, 240), (255, 0, 0), 5)
                    cv2.rectangle(img, (((centerx1+centerx2)/2), 240), (((centerx1+centerx2)/2), 240), (255, 0, 0), 5)
                    cv2.rectangle(img, (((centerx1+centerx2)/2), ((centery1+centery2)/2)), (((centerx1+centerx2)/2), ((centery1+centery2)/2)), (255, 0, 0), 5)


                #processes distance and angle from a boiler
                if visionState:
                    logging.info('Processing contour attributes as boiler...')
                    #distinguishes between boiler and gear targets ***DEPRECATED***
                    #print 'Looking for boiler target...'
                    #print valComparator(x1, x2, 50)
                    #print h1 < w1
                    #if valComparator(x1, x2, 50) and h1 < w1:
                    angle = getBoilerAngle(centerx1)
                    #print 'BoilerAngle: ' + str(angle)
                    dist = getBoilerDist(w1, h1, y1, 0)
                #    print 'BoilerDist: ' + str(dist)
                    offset = 0
                    target = True
                    logging.info('Done')
                    #else:
                    #print 'No boiler target found'

                #processes distance and angle from a gear
                if visionState == False:
                    logging.info('Processing contour attributes as gear...')
                    #distinguishes between boiler and gear targets ***DEPRECATED***
                    #print 'Looking for gear target...'
                    #print valComparator(centery1, centery2, 50)
                    #print (abs(h1-h2) <= 100)
                    #if valComparator(centery1, centery2, 50) and (abs(h1-h2) <= 100):
                    angle = getGearAngle(float(centerx1+centerx2)/2)
                    #print 'GearAngle: ' + str(angle)
                    dist = getGearDist(float(h1 + h2)/2)
                    #print 'GearDist: ' + str(dist)
                    offset = 0
                    target = True
                    logging.info('Done')
                    #else:
                        #print 'No gear target found'
                #returns null if contou1rs don't pass criteria for their respective target types ***DEPRECATED***
                #else:
                    #dist = 0
                    #angle = 0
                    #offset = 0
                    #target = False
            #returns null values if not enough contours are found
            else:
                logging.info('Not enough contours')
                dist = 0
                angle = 0
                offset = 0
                target = False
            if isDebugging:
                cv2.imshow('image', img)
                cv2.imshow('hsl', hsl)

            #posts values to the SmartDashboard and crontab
            if isNetworked:
                logging.info('Publishing to networktables')
                sd.putNumber('angle', angle)
                sd.putNumber('dist', dist)
                sd.putBoolean('targetInFrame', target)
                NetworkTables.flush()


def manageCameras():
    global isNetworked
    global isDebugging
    global isVisionStateLocked
    global boilerCam
    global gearCamAddr
    global boilerCamAddr
    global gearCamAddr
    global sharedImageTuple
    global isNewFrame
    logging.info('Camera Thread initialized')
    while True:
        try:
            #print 'Getting target type...'
            if isNetworked and isVisionStateLocked == False:
                visionState = sd.getBoolean('visionTarget')
            #print "visionState" + str(visionState)
            #print 'Target type found'
            #print visionState
        except:
            visionState = False
            #pulls frame from boiler camera if that is requested, attempts to reconnect if no frame is available
        if visionState:
            logging.info('Retrieving frame from BoilerCam...')
            if boilerCam != False:
                retval, img = boilerCam.read()
                #print 'Image Retrieved from boilerCam'
            else:
                logging.warning('Image Retrieval from BoilerCam Failed!')
                connectCamera(boilerCamAddr, 'Boiler', 1)
                continue


        #pulls frame from gear camera if that is requested, attempts to reconnect if no frame is available
        else:
            logging.info('Retrieving frame from GearCam...')
            if gearCam != False:
                retval, img = gearCam.read()
                #print 'Image Retrieved from gearCam'
            if gearCam == False or retval == False:
                logging.warning('Image retrieval from GearCam failed!')
                connectCamera(gearCamAddr, 'Gear', 1)
                continue
        if retval:
            logging.info('Frame retrieved, publishing...')
            sharedImageTuple.write((img, visionState))
            isNewFrame.write(True)
        else:
            logging.warning('Frame unusable!')

#***CHANGE CAMERA MJPEG ADDRESSES HERE******************************************************************************************************************************************
boilerCamAddr = 'http://10.13.91.3/axis-cgi/mjpg/video.cgi?.mjpg'
gearCamAddr = 'http://10.13.91.6/axis-cgi/mjpg/video.cgi?.mjpg'
#*****************************************************************************************************************************************************************************
logging.basicConfig(filename=(str(datetime.datetime.now())+'.log'), level=logging.INFO, format='%(levelname)s:%(message)s')
time.sleep(10)

isDebugging = False
targetSide = 0
isNetworked = True
isVisionStateLocked = False

if (len(sys.argv) > 1):
    for arg in sys.argv:
        if arg == 'debug':
            isDebugging = True
            #cv2.startWindowThread()
            cv2.namedWindow("image")
            cv2.namedWindow('hsl')
            #Opens default camera for ONLY code debugging on laptop
        if arg == 'nonetworktables':
            isNetworked = False
        if arg == 'gear':
            isVisionStateLocked = True
            visionState = False
        if arg == 'boiler':
            isVisionStateLocked = True
            visionState = True
        if arg == 'webcam':
            gearCamAddr = 0
            boilerCamAddr = 0
        arglist = list(arg)
        if (len(list(arg)) >= 12) and ''.join(arglist[:12]) == 'gearaddress=':
            gearCamAddr = ''.join(arglist[12:])
        if (len(list(arg)) >= 14) and ''.join(arglist[:14]) == 'boileraddress=':
            boilerCamAddr = ''.join(arglist[14:])

#Initializes the NetworkTable class at the roboRIO IP connects to Smart Dashboard
if isNetworked:
    NetworkTables.initialize(server='10.13.91.2')
    NetworkTables.setWriteFlushPeriod(30)
    sd = NetworkTables.getTable('SmartDashboard')

#connects to cameras using the connectCamera() function
boilerCam = connectCamera(boilerCamAddr, 'Boiler', 5)
gearCam = connectCamera(gearCamAddr, 'Gear', 5)

#Instantiates the GRIP generated pipeline
pipe = GripPipeline()

sharedImageTuple = MultiThreadVariable((None, None))
isNewFrame = MultiThreadVariable(False)
#prints version number for idiot proofing
print 'MooseVision 4.1'

cameraThread = threading.Thread(target=manageCameras)
computeThread = threading.Thread(target=manageProcessing)

print 'ping'
logging.info('Initializing Camera Thread...')
cameraThread.start()
print 'pong'
logging.info('Initializing Computation Thread...')
computeThread.start()

print 'finished initialization'
