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
import globalvar
import os
import thread
import logging
import ConfigParser
from logging import handlers
import cherrypy
import f1reader
from f1status import f1TrackStatus

log  = logging.getLogger('live-f1')

class f1live( object ):
    def __init__( self ):
        self.config = ConfigParser.RawConfigParser()
        self.readConfig()
        logfilename = self.config.get( 'log', 'file' )
        logfilesize = self.config.getint( 'log', 'logsize' )
        logbackups  = self.config.getint( 'log', 'logbackup' )

        file_log_handler = handlers.RotatingFileHandler( logfilename, logfilesize, logbackups )
        log.addHandler( file_log_handler )

        # nice output format
        formatter = logging.Formatter( '%(asctime)s - %(module)s - %(levelname)s - %(message)s' )
        file_log_handler.setFormatter( formatter )
        log.setLevel( 10 )    
        log.info( 'Starting the application' )
        thread.start_new( f1reader.Reader, ( self, ) )

        return
    # end constructor    
    
    def readConfig( self ):
        self.config.read( 'userf1.conf' )
        return
            
    def writeConfig( self ):
        self.config.write( 'userf1.conf' )
        return
    
    def header( self, title ):
        return ( """<!DOCTYPE html><html><head><title>Live F1 timing</title>
                    <meta http-equiv='refresh' content='5'>
                    <link rel='stylesheet' type= 'text/css' href='/livef1.css' />
                    <link rel='icon' type='image/ico' href='/images/favicon.ico'>
                    %s</head><body>""" % ( title ) )

    def trailer( self, trail ):
	   return ( "<div class='trailer'><h3>%s</h3></div></body></html>" % trail )
    # end def
        
    def index( self ):
        yield self.header( "<h1>Live F1 timing</h1>" )
        yield globalvar.board.gethtml( 'contents' )
        yield globalvar.TrackStatus.getHtml( 'status' )
        yield globalvar.commentary.gethtml( 'comment' ) 
        yield self.trailer( globalvar.TrackStatus.Copyright )
    # end def
    index.exposed = True

    def time( self ):
        yield self.header( "" ) 
        yield globalvar.board.gethtml( 'contents_wide' )
        yield self.trailer( globalvar.TrackStatus.Copyright )
    # end def

    time.exposed = True

    def comment( self ):
        yield self.header( "" )         
        yield globalvar.commentary.gethtml( 'comment_wide' )
        yield self.trailer( globalvar.TrackStatus.Copyright )
        return
    # end def
    comment.exposed = True
    
    def status( self ):
        yield self.header( "" )
        yield globalvar.TrackStatus.getHtml( 'status_wide' )
        yield self.trailer( globalvar.TrackStatus.Copyright )      
    # end def
    status.exposed = True
    
    def critical( self, data ):
        self.__log.critical( data )            
    # end def

    def error( self, data ):
        self.__log.error( data )            
    # end def

    def warn( self, data ):
        self.__log.warn( data )            
    # end def

    def info( self, data ):
        self.__log.info( data )            
    # end def

    def debug( self, data ):
        self.__log.debug( data )            
    # end def   
    # B9 7D 9F 20
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
                log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )
                hexstr  = ''
                ascii   = ''
                cnt     = 0
                idx     = idx + 16       
            # endif
        # next
        if 0:
            log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )                            
        # endif
        return 
    # end def 
#end class
    
# cherrypy needs an absolute path to deal with static data
globalvar.theApp    = f1live()
globalvar.TrackStatus = f1TrackStatus()

cherrypy.quickstart( globalvar.theApp, '/', config = os.path.join( os.path.join( os.getcwd(), 
                                            os.path.dirname( __file__ ) ), 'livef1.conf' ) )
