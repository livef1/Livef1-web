#
#   livef1
#
#   capLiveF1.py - Capture event data from Formula 1 and store into
#                  event directory.
#
#   Copyright (c) 2014 Marc Bertens <marc.bertens@pe2mbs.nl>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#   
#   Special thanks to the live-f1 project 'https://launchpad.net/live-f1'
#   * Scott James Remnant
#   * Dave Pusey
#
#   For showing the way of program logic.   
#
import os
import sys
import cherrypy
import logging
import ConfigParser
from logging import handlers

from src.reader import StreamReaderThread

__version__ = "0.1"
__applic__  = "Live F1 Capture"
__author__  = "Marc Bertens"

class CaptureLiveF1( object ):
    def __init__( self ):
        self.log  = logging.getLogger('live-f1')
                 
        self.config = ConfigParser.RawConfigParser()
        self.config.read( 'CaptureLiveF1.conf' )
        directory = os.path.join( os.path.dirname( __file__ ), self.config.get( 'log', 'dir' ) )
        if not os.path.exists( directory ):
            os.makedirs( directory )
        # end if
        file_log_handler = handlers.RotatingFileHandler( os.path.join( directory, self.config.get( 'log', 'file' ) ), 
                                                        maxBytes=self.config.getint( 'log', 'size' ), 
                                                        backupCount=self.config.getint( 'log', 'backup' ) )

        self.log.addHandler( file_log_handler )
        # nice output format
        formatter = logging.Formatter( '%(asctime)s - %(module)s - %(levelname)s - %(message)s' )
        file_log_handler.setFormatter( formatter )
        self.log.setLevel( self.config.getint( 'log', 'level' ) )
            
        self.log.info( 'Starting the application' )
        self.readerThread       = StreamReaderThread( "live-reader", self )
    # endif

    def readFiles( self, rootdir ):
        result = []
        for root, subFolders, files in os.walk( rootdir ):
            for f in files:
                showFile = os.path.join( os.path.join( root, f ) ) 
                self.log.info( "file: %s" % ( showFile ) )
                result.append( ( showFile, root, f ) )
            # next   
        # next
        return result 
        
    def readDir( self, rootdir ):
        result = []
        for root, subFolders, files in os.walk( rootdir ):
            self.log.info( "root: %s" % root )
            for folder in subFolders:
                showFolder = os.path.join( root, folder )
                self.log.info( "folder: %s" % showFolder )
                result += self.readFiles( showFolder )
            # next
        # next
        return result
    # end def        

    def index( self ):
        files = self.readDir( self.config.get( 'keyframe', 'dir' ) )
        yield """<!DOCTYPE html><html><head><title>%s</title>
                    <meta http-equiv='REFRESH' content='10'>
                    <link rel='stylesheet' type= 'text/css' href='/livef1.css' />
                    <link rel='icon' type='image/ico' href='/images/favicon.ico'>
                    <h2>%s</h2></head><body>""" % ( __applic__, __applic__ )
        yield "<ul>"
        for file in files:
            yield "<li><a href='%s'>%s</li>" % ( file[ 0 ], file[ 2 ] ) 
        # next 
        yield "</ul>"
        yield "<div class='trailer'><h3>Live F1 Capture: Copyright 2014 by Marc Bertens, all rights reserved.</h3></div></body></html>"
        return         
    index.exposed = True
        
"""
    This is to stop the reader thread
"""      
def StopReaderThread():
    theApp.readerThread.join()
    return
# end if    

StopReaderThread.priority = 10
cherrypy.engine.subscribe( 'stop', StopReaderThread )        

# cherrypy needs an absolute path to deal with static data
theApp        = CaptureLiveF1()

cherrypy.quickstart( theApp, '/', config = os.path.join( os.path.join( os.getcwd(), 
                                            os.path.dirname( __file__ ) ), 'capLiveF1.conf' ) )
