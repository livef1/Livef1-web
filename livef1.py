#!/usr/bin/python
#
#   livef1
#
#   livef1.py - Main program file
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
import cherrypy
import logging
import ConfigParser
from logging import handlers

from src.reader import StreamReaderThread

from src.status import GetTrackStatus
from src.drivers import GetBoard
from src.comment import GetCommentary

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

class F1LiveServer( object ):
    def __init__( self, config_file ):
        self.log  = logging.getLogger('live-f1')
        self.TrackStatus    = GetTrackStatus()
        self.board          = GetBoard()
        self.commentary     = GetCommentary()
        self.config = ConfigParser.RawConfigParser()
        self.config.read( config_file )
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
        self.RefreshRate        = 5
        self.loadingKeyframe    = False
        self.interpolateNext    = False
        self.readerThread       = StreamReaderThread( "live-reader", self )
        return
    # end constructor    
   
    def header( self, title ):
        interval = self.readerThread.Interval
        return ( """<!DOCTYPE html><html><head><title>%s</title>
                    <meta http-equiv='REFRESH' content='%i'>
                    <link rel='stylesheet' type= 'text/css' href='/livef1.css' />
                    <link rel='icon' type='image/ico' href='/images/favicon.ico'>
                    <h2>%s</h2></head><body>""" % ( title, interval, title ) )

    def trailer( self, trail ):
	   return ( "<div class='trailer'><h3>LiveF1Web: Copyright 2014 by Marc Bertens, all rights reserved, Timing info: %s</h3></div></body></html>" % trail )
    # end def
        
    def index( self ):
        yield self.header( "Live F1 Web - Timing" )
        yield self.board.gethtml( 'contents' )
        yield self.TrackStatus.getHtml( 'status' )
        yield self.commentary.gethtml( 'comment' ) 
        yield self.trailer( self.TrackStatus.Copyright )
    # end def
    index.exposed = True

    def drivers( self ):
        yield self.header( "" ) 
        #self.board.dump()
        yield self.board.gethtml( 'contents_wide' )
        yield self.trailer( self.TrackStatus.Copyright )
    # end def
    drivers.exposed = True

    def comment( self ):
        yield self.header( "" )         
        yield self.commentary.gethtml( 'comment_wide' )
        yield self.trailer( self.TrackStatus.Copyright )
        return
    # end def
    comment.exposed = True
    
    def status( self ):
        yield self.header( "" )
        yield self.TrackStatus.getHtml( 'status_wide' )
        yield self.trailer( self.TrackStatus.Copyright )      
    # end def
    status.exposed = True
        
    def hexDebug( self, title, data, length = -1 ):
        hexstr  = ''
        ascii   = ''
        cnt = 0
        idx = 0
        if length != -1:
            if length >= len( data ):
                length = len( data ) - 1
            # endif
            data = data[ 0 : length ]            
        # endif
        for c in data:
            hexstr = hexstr + "%02X " % ( ord( c ) )
            if ord( c ) < 0x20 or ord( c ) > 0x7F: 
                ascii = ascii + '.'
            else:                
                ascii = ascii + c
            # endif                
            cnt = cnt + 1
            if ( cnt == 16 ):
                self.log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )
                hexstr  = ''
                ascii   = ''
                cnt     = 0
                idx     = idx + 16       
            # endif
        # next
        if 0:
            self.log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )                            
        # endif
        return 
    # end def 
# end class

# cherrypy needs an absolute path to deal with static data

theApp        = F1LiveServer( 'userf1.conf' )
# theApp        = F1LiveServer( 'testLiveF1.conf' )
"""
    This is to stop the reader thread
"""      
def StopReaderThread():
    theApp.readerThread.join()
    return
# end if    

StopReaderThread.priority = 10
cherrypy.engine.subscribe( 'stop', StopReaderThread )

cherrypy.quickstart( theApp, '/', config = os.path.join( os.path.join( os.getcwd(), 
                                            os.path.dirname( __file__ ) ), 'livef1.conf' ) )