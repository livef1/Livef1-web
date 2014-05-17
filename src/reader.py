#
#   livef1
#
#   f1reader.py - reader task running under the web-server
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
from time import sleep
import threading
import logging
import src.session

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

class ReaderThread( threading.Thread ):
    def __init__( self, name, theApp ):
        threading.Thread.__init__( self )
        self.Name       = name
        self.theApp     = theApp;
        self.log        = logging.getLogger( 'live-f1' )
        self.running    = 0
        self.Session    = None
        self.Interval   = 1
        self.error      = ''
        self.start()
        return
    # end def
    
    def run( self ):
        self.running    = 1
        tries           = 0
        local_running   = 1
        while self.running and local_running:
            self.log.info( "Starting the HTTP stream running %i, tries %i" % ( self.running, tries ) ) 
            self.Session.parse( self.Session.obtain_key_frame() )
            self.log.info( "Opening the STREAM session, running %i, tries %i" % ( self.running, tries ) ) 
            if ( self.Session.open() ):
                self.log.info( "Session opened, running %i, tries %i" % ( self.running, tries ) ) 
                self.Interval = 1
                while ( self.running and self.Session.read() > 0 ):
                    self.Interval = self.Session.pollCount
                    if self.Interval < 1:
                        # set the minimum HTTP refresh rate
                        self.Interval = 1
                    elif self.Interval > 10:
                        # set the maximum HTTP refresh rate  
                        self.Interval = 10                       
                    # end if
                    # self.log.info( "running %i, tries %i, interval: %i" % ( self.running, tries, self.Interval ) )                          
                    continue
                # end while
                #
                #   Posible to get here from a decryption error, so just recycle the session 
                self.Session.close()
                tries = 0
            else:   
                # stop the thread for now
                self.log.error( "Error %s, connecting, try %i of 5" % ( self.error, tries ) )
                if tries > 5:
                    local_running = 0
                else:
                    tries += 1
                # end if     
            # end if  
        # end while
        return;
    # end def
    
    def join( self, timeout = None ):
        if self.running: 
            self.running = 0
            self.log.warning( "%s: stopping" % ( self.Name ) )
            if timeout:
                threading.Thread.join( self, timeout )
            else:
                threading.Thread.join( self )
            # end if
        # end if                                    
        return
    # end def
# end class 

class StreamReaderThread( ReaderThread ):
    def __init__( self, name, theApp ):
        ReaderThread.__init__( self, name, theApp )
        return
    # end def 

    def run( self ):
        self.log.info( '%s: Live F1 STREAM reader thread starting ...' % ( self.Name ) )
        self.running    = 1
        tries           = 0
        while self.running:
            self.Session = src.session.f1StreamSession( self.theApp, self.log )            
            key_val = self.Session.obtain_auth_cookie()
            if not key_val:
                self.log.error( "Error getting cookie, try %i of 5" % tries )
                tries   += 1
            else:
                self.log.info( "Got authentication cookie: %s" % ( key_val ) )
                tries   = 0
            # end if   
            if key_val:               
                ReaderThread.run( self )
                tries   = 0
            self.log.error( "Error getting cookie, try %i of 5" % tries )
            if tries > 5:
                self.running = 0
            #end if
        # end while
        self.log.warning( "%s: Exiting the THREAD" % ( self.Name ) )
        exit()    
        return
    # end def
# end class 

class FileReaderThread( ReaderThread ):
    def __init__( self, name, theApp ):
        ReaderThread.__init__( self, name, theApp )
        return
    # end def 

    def run( self ):
        self.log.info( '%s: Live F1 FILE reader thread starting ...' % ( self.Name ) )
        self.Session = f1stream.f1FileSession( self.theApp, self.log, 'Qualifying-E007340' )            
        ReaderThread.run( self )
        self.log.warning( "%s: Exiting the THREAD" % ( self.Name ) )
        exit()    
        return
    # end def
# end class 

