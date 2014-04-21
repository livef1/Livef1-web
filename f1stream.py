#
#   livef1
#
#   f1stream.py - Data stream and packet handling
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
import array
import socket
import select
import httplib2
import urllib
import urllib2
import Cookie
import globalvar
from f1comment import f1commentary, f1text
from f1drivers import f1Board
from f1crypt import f1Crypto
from f1status import f1TrackStatus 
import logging

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

log  = logging.getLogger('live-f1')

CRYPTO_SEED         = 0x55555555
LOGIN_URL	    	= "/reg/login"
REGISTER_URL		= "/reg/registration"
KEY_URL_BASE		= "/reg/getkey/"
KEYFRAME_URL_PREFIX	= "/keyframe"

class SYS( object ):
    EVENT_ID        = 1
    KEY_FRAME		= 2
    VALID_MARKER	= 3
    COMMENTARY		= 4
    REFRESH_RATE	= 5
    NOTICE		    = 6
    TIMESTAMP		= 7
    WEATHER		    = 9
    SPEED		    = 10
    TRACK_STATUS	= 11
    COPYRIGHT		= 12

# RACE_EVENT             = 0
# PRACTICE_EVENT         = 1
# QUALIFYING_EVENT       = 2

class CAR( object ):
    POSITION_UPDATE     = 0
    RACE_POSITION       = { 1:  1, 2:  1, 3:  1 } 
    DRIVER_NUMBER       = { 1:  2, 2:  2, 3:  2 }
    RACE_DRIVER         = { 1:  3, 2:  3, 3:  3 }
    GAP                 = { 1:  4, 2:  5, 3: 99 } 
    INTERVAL            = { 1:  5, 2: 99, 3: 99 }
    LAP_TIME            = { 1:  6, 2:  4, 3: 99 } 
    SECTOR_1            = { 1:  7, 2:  6, 3:  7 }
    SECTOR_2            = { 1:  9, 2:  7, 3:  8 }
    SECTOR_3            = { 1: 11, 2:  8, 3:  9 }
    PIT_LAP_1           = { 1:  8, 2: 99, 3: 99 }
    PIT_LAP_2           = { 1: 10, 2: 99, 3: 99 }   
    LAP                 = { 1: 99, 2:  9, 3: 10 }
    PERIOD_1            = { 1: 99, 2: 99, 3:  4 }
    PERIOD_2            = { 1: 99, 2: 99, 3:  5 }
    PERIOD_3            = { 1: 99, 2: 99, 3:  6 }
    POSITION_HISTORY    = 15

class SYS_SPEED( object ):
    SPEED_SECTOR1	= 1
    SPEED_SECTOR2	= 2
    SPEED_SECTOR3	= 3
    SPEED_TRAP		= 4
    FL_CAR			= 5
    FL_DRIVER		= 6
    FL_TIME			= 7
    FL_LAP			= 8

class f1packet( object ):
    def __init__( self, theApp ):
        self.car                = 0
        self.type               = 0
        self.length             = 0
        self.data               = 0
        self.payload            = bytes()
        self.__theApp           = theApp
        self.crypto             = f1Crypto( self.__theApp )
        return
    # end def 

    def __SwapValueLength( self ):
        tmp         = self.value
        self.value  = self.length
        self.length = tmp
        return        
        
    def set( self, stream ):
        if stream.len() < 2:
            self.type       = 0
            self.car        = 0
            self.type       = 0
            self.length     = 0
            self.data       = 0
            self.payload    = None            
            return ''
        # end if 
        block = stream.read( 2 )
        b0 = ord(block[ 0 ])         
        b1 = ord(block[ 1 ])
        self.car        = ( b0 & 0x1F );
        self.type       =  ( ( b0 & 0xE0 ) >> 5 & 0x7 | ( b1 & 0x1) << 3 );
        self.data       =  ( ( b1 & 0x0E ) >> 1 );
        self.length     =  ( ( b1 & 0xF0 ) >> 4 );
        self.value      =  ( ( b1 & 0xFE ) >> 1 );        
        decrypt = False                                    
        if self.car == 0:
            if self.type == SYS.EVENT_ID:
                self.payload    = array.array( 'B', stream.read( self.length ) )
                log.debug( "f1packet: SYS.EVENT_ID" )
            elif self.type == SYS.KEY_FRAME:
                self.payload    = array.array( 'B', stream.read( self.length ) )
                log.debug( "f1packet: SYS.KEY_FRAME" )               
            elif self.type == SYS.VALID_MARKER:
                log.debug( "f1packet: SYS.VALID_MARKER" )
                if not self.length == 0:
                    log.debug(  "Long valid marker" )
                # end if          
                self.payload    = None
            elif self.type == SYS.REFRESH_RATE:
                log.debug( "f1packet: SYS.REFRESH_RATE" )
                self.payload    = None             
            elif self.type == SYS.TIMESTAMP:
                log.debug( "f1packet: SYS.TIMESTAMP" )
                decrypt         = True
                self.length     = 2
                self.payload    = array.array( 'B', stream.read( self.length ) )
            elif self.type == SYS.WEATHER:
                log.debug( "f1packet: SYS.WEATHER" )
                if self.length < 15:
                    decrypt = True
                    self.payload = array.array( 'B', stream.read( self.length ) )
                else:
                    if self.__theApp.loadingKeyframe:
                        self.__theApp.interpolateNext    = True
                    # end if                                                                
                # end if
                self.payload    = None
            elif self.type == SYS.SPEED:
                log.debug( "f1packet: SYS.SPEED" )
                decrypt = True
                self.payload = array.array( 'B', stream.read( self.value ) )
            elif self.type == SYS.TRACK_STATUS:
                log.debug( "f1packet: SYS.TRACK_STATUS" )
                decrypt = True
                self.payload = array.array( 'B', stream.read( self.length ) )
            elif self.type == SYS.NOTICE:
                self.__SwapValueLength()
                log.debug( "f1packet: SYS.NOTICE" )
                decrypt = True
                self.payload = array.array( 'B', stream.read( self.length ) )
            elif self.type == SYS.COPYRIGHT:
                self.__SwapValueLength()
                log.debug( "f1packet: SYS.COPYRIGHT length = %i" % ( self.length ) )
                self.payload = array.array( 'B', stream.read( self.length ) )
            elif self.type == SYS.COMMENTARY:
                self.__SwapValueLength()
                log.debug( "f1packet: SYS.COMMENTARY length = %i" % ( self.length ) )
                self.payload = array.array( 'B', stream.read( self.length ) )
                decrypt = True                                 
            else:
                # unhandled packet type
                log.error( "f1packet: Unhandled packet type %i" %  ( self.type ) )                            
            # end if                                            
        else:
            if self.type == 0:
                self.payload        = None           
            elif self.type == 15:               
                self.__SwapValueLength()
                if self.length:                 
                    self.payload    = array.array( 'B', stream.read( self.value ) )        
                    decrypt         = True
                else:
                    self.payload    = None                
                # end if
            else:
                decrypt             = True
                if self.length:                 
                    self.payload    = array.array( 'B', stream.read( self.length ) )               
                else:
                    self.payload    = None
                # end if
            # end if                
        # end if
        log.debug( "f1packet: (%X,%X), type: %i, car %i, data: %i, len: %i, value: %s" % ( 
                            b0, b1, self.type, self.car, self.data, self.length, self.value ) )

        if decrypt and self.payload:
            self.payload = self.crypto.decryptBlock( self.payload ) 
            log.debug( "Decrypted : %s" % ( self.payload2hexstr() )  )
        # end if                            
        return 
    # end def 
    
    def payload2hexstr( self, off = 0 ):
        hexstr = ""
        if self.payload:
            for c in self.payload[ off : self.length ]:
                hexstr = hexstr + "%02X " % ( c )
            # next
        # end if            
        return hexstr 
    # end def
    
    def payload2str( self, off = 0 ):
        tmpstr = ""
        if self.payload:
            for c in self.payload[ off : self.length ]:
                tmpstr = tmpstr + "%c" % ( c )
            # next
        # end if            
        return tmpstr 
    # end def
            
    def payload2int( self, off = 0 ):
        val = 0
        if self.payload:
            shift = 0
            for c in self.payload[ off : self.length ]:
                val = val | ( c << shift ) 
                shift = shift + 8
            # next            
        # end if            
        return val
    # end def
# end class
    
globalvar.commentary    = f1commentary()
globalvar.board         = f1Board()
 
class f1Stream( object ):
    def __init__( self ):
        self.__data     = None
        self.__length   = 0
        self.__index    = 0
        return

    def Clear( self ):
        self.__data     = None
        self.__length   = 0
        self.__index    = 0
        return
                
    def len( self ):
        return self.__length - self.__index                
                
    def Set( self, block, length = -1 ):
        if length == -1:
            length  = len( block )
        # end if            
        self.__data     = block
        self.__length   = length
        self.__index    = 0        
        return
    
    def read( self, length ):
        data = self.__data[ self.__index : self.__index + length ]
        self.__index += length                                 
        return data 
 
 
class f1session( object ):
    auth_http_host		= 'live-timing.formula1.com'
    auth_http_port 		= 80
    data_host		    = 'live-timing.lb.formula1.com'
    data_port		    = 4321
    
    def __init__( self, theApp, user, passwd ):
        self.__username         = user
        self.__password         = passwd
        self.__theApp           = theApp
        self.packet             = f1packet( theApp )
        self.__http             = httplib2.Http()
        self.__cookie           = None
        self.__timer            = 0
        self.pollCount          = 0
        self.frame              = 0
        self.__COOKIE_VALUE     = None
        self.__timestamp        = 0
        self.__comment          = f1text() 
        self.error              = 0
        self.__stream           = f1Stream()
        self.__decryption_error = 0
        self.__refreshRate      = 100
        self.__StoreData        = ( self.__theApp.config.get( 'keyframe', 'store' ) == "True" )
        self.__keyPath          = os.path.join( os.path.dirname( __file__ ), self.__theApp.config.get( 'keyframe', 'dir' ) )
        self.keyframe           = None      
        self.packet.crypto.reset()
        return

    def obtain_auth_cookie( self ):
        headers = { "Content-Type": "application/x-www-form-urlencoded" }
        body = { 'email': self.__username, 'password': self.__password }
        url = 'http://%s:%s%s' % ( self.auth_http_host, self.auth_http_port, LOGIN_URL )
        log.info( "REQ: %s  %s" % ( url, urllib.urlencode( body ) ) ) 
        response, content = self.__http.request( url, 'POST', headers=headers, body=urllib.urlencode(body))
        log.debug( "RESP: %s" % ( response ) )
        # log.debug( "DATA: %s" % ( content ) )
        if response[ 'status' ] == '200' or response[ 'status' ] == '302':
            self.__cookie = response[ 'set-cookie' ]
            C = Cookie.BaseCookie( self.__cookie )
            for k, v in C.items():
                if ( k == "USER" ): 
                    self.__COOKIE_VALUE = v.value
                # end if
            # end for 
            log.debug( "Cookie.USER = %s" % ( self.__COOKIE_VALUE ) )
            return self.__COOKIE_VALUE
        # endif
        return ""

    def obtain_key_frame( self, number = 0 ):
        if number > 0:
            self.frame = number;
            url = "http://%s:%i%s_%05d.bin" % ( self.auth_http_host, self.auth_http_port, KEYFRAME_URL_PREFIX, self.frame )
        else:
            url = 'http://%s:%s%s.bin' % ( self.auth_http_host, self.auth_http_port, KEYFRAME_URL_PREFIX )
            self.frame = number
        # end if
        log.info( "REQ: %s" % ( url ) ) 
        response, content = self.__http.request( url, 'GET' )
        log.debug( "RESP: %s" % ( response ) )
        # end if            
        if response[ 'status' ] == '200':
            # self.__theApp.hexDebug( "KEYFRAME", content )
            if self.__StoreData:
                if self.keyframe:
                    self.keyframe.close()
                    self.keyframe = None                    
                # end if
                directory = os.path.join( self.__keyPath, "F%06i" % ( self.frame ) )
                if not os.path.exists( directory ):
                    os.makedirs( directory )
                # end if
                filename = os.path.join( directory, 'keyframe_http_%04X.bin' % self.__timestamp ) 
                if not os.path.isfile( filename ):               
                    self.keyframe = open( filename, 'wb+', 0 )
                    self.keyframe.write( content )
                    self.keyframe.close()
                    self.keyframe = None
                # end if 
                filename = os.path.join( directory, 'keyframe_ts_%04X.bin' % self.__timestamp ) 
                if not os.path.isfile( filename ):               
                    self.keyframe = open( filename, 'wb+', 0 )
                # end if                    
            # end if
            return content           
        return "" 

    def obtain_decryption_key( self ):
        url = "http://%s:%s%s%u.asp?auth=%s" % ( self.auth_http_host, self.auth_http_port, KEY_URL_BASE, self.eventid, self.__COOKIE_VALUE )
        response, content = self.__http.request( url, 'GET' )
        #log.debug( "RESP: %s" % ( response ) )
        log.debug( "DATA: %s" % ( content ) )
        if self.__StoreData:
            directory = os.path.join( self.__keyPath, "F%06i" % ( self.frame ) )
            if not os.path.exists( directory ):
                os.makedirs( directory )
            filename = os.path.join( directory, 'keyframe.key' )
            # end if
            if not os.path.isfile( filename ):
                key = open( filename, 'wb+', 0 )
                key.write( content )
                key.close()
            # end if
        # end if            
        return content
        
    def open( self ):
        log.debug( "Connecting: %s:%s" % ( self.data_host, self.data_port ) )
        addrlist = socket.getaddrinfo( self.data_host, self.data_port, 0, 0, socket.SOL_TCP )
        for addr in addrlist:
            self.sock = socket.socket( addr[0], addr[1], addr[2] );
            if ( self.sock ):
                self.error = self.sock.connect_ex( addr[ 4 ] );
                log.debug( "open.connect_ex: %s" % ( self.error ) )
                self.__decryption_error = 0
                if ( self.error == 0 ):
                    self.pollCount = 0
                    return True
            self.sock.close() 
        self.error = -1
        return False

    def close( self ):
        self.sock.close()
        self.error = 0
        return 

    def read( self ):
        # Map file descriptors to socket objects
        fd_to_socket = { self.sock.fileno(): self.sock, }
        poller = select.poll() 
        poller.register( self.sock, select.POLLIN | select.POLLHUP | select.POLLERR | select.POLLNVAL )
        events = poller.poll( self.__refreshRate )
        for fd, flag in events:
            if flag & select.POLLIN:
                buff = fd_to_socket[ fd ].recv( 512 );
                if buff:
                    # data
                    if self.keyframe: 
                        self.keyframe.write( buff )
                    # end if
                    self.parse( buff )
                    self.__timer = 0
                    if self.__decryption_error > 3:
                        poller.unregister( self.sock )
                        log.info( "Close : Due to decryption error" )
                        self.close()
                        return False
                    self.pollCount = 0
                    return True
                else:
                    # Interpret empty result as closed connection
                    poller.unregister( self.sock )
                    log.debug( "Close : #1" )
                    self.close()
                    self.error = -1
                    return False   
            elif flag & select.POLLHUP:
                # Client hung up
                poller.unregister( self.sock )
                self.close()
                log.debug( "Close : #2" )
            elif flag & select.POLLERR:
                # Error
                poller.unregister( self.sock )
                self.close()
                log.debug( "Close : #3" )
            else:
                # something else just ignore
                log.debug( "Else : #1" )
            # endif
        # next    
        self.__timer = self.__timer + 1
        #log.debug( "Timeout : %i" % self.__timer )
        if self.__timer < 10:   # 10 seconds
            return True
        # endif
        # Timeout ?
        b = bytes( "\x10" ) 
        self.pollCount += 1
        #if ( self.pollCount % 10 ) == 0:
        #    globalvar.board.dump()
        # end if
        if self.pollCount >= 60: # 600 seconds
            return False
        # endif
        length = self.sock.send( b )
        log.debug( "Send : %s, length : %i, pollCount %i, RefreshRate %i" % ( b, length, self.pollCount, self.__refreshRate ) )
        if length > 0:
            # Reset the timer value.
            self.__timer = 0
            # return true to continue 
            return True
        # endif
        return False
    
    def HandleSysEventId( self ):
        event_sub_type = 0
        if self.packet.length > 0:                     
            event_sub_type = self.packet.payload[ 0 ] 
        if event_sub_type == 2:
            log.info( "SYS.EVENT_ID : (str) %s" % ( self.packet.payload2str( 1 ) ) )
            if self.packet.payload[ 1 ] == 0x5F:
                log.info( "SYS.EVENT_ID : (date) %s" % ( self.packet.payload2str( 2 ) ) )
            else:
                self.eventid        = int( self.packet.payload2str( 1 ) )
                globalvar.TrackStatus.reset()                    
                globalvar.TrackStatus.Event	= self.packet.data
                globalvar.TrackStatus.EventId  = self.eventid
                globalvar.commentary.reset()
                log.info( "SYS.EVENT_ID : %i" % ( self.eventid ) )
                self.packet.crypto.setKey( int( self.obtain_decryption_key(), 16 ) )                        
            # endif
        else:
            log.error( "SYS.EVENT_ID unknown sub type %i" % ( event_sub_type ) )
        # endif
        return  
    
    def HandleSysKeyFrame( self ):
        last    = self.frame 
        number = self.packet.payload2int()
        log.debug( "Current keyframe: %i, requesting keyframe: %i" % ( self.frame, number ) )
        #if self.__decryption_error > 3:
        #   self.frame = self.frame - 1  
        #   if self.frame < 0:
        #       self.frame = 0 
        #   # end if
        # end if
        length = 0 
        self.packet.crypto.reset()
        if not self.frame == number:
            # now obtain the key
            log.info( "Loading new keyframe" )
            block = self.obtain_key_frame( number )
            length = len( block )                          
            self.parse( block )
            self.__decryption_error = 0
            self.packet.crypto.reset() 
        else:
            log.info( "Stay at current keyframe" )                         
        # endif
        self.frame = number
        log.info( "SYS.KEY_FRAME : %i (%X), last : %i (%X), block-length %i" % ( 
                        self.frame, self.frame, last, last, length ) )
        return        
    
    def HandleSysComment( self ):
        clock = ""
        text = self.packet.payload2str( 2 )
        log.info( "System.Commentary : %s" % ( text ) )
        if len( text ) > 8:
            if text[ 2 ] == ':': 
                if text[ 5 : 8 ] == ' - ':
                    clock   = text[ 0 : 5 ]
                    text    = text[ 8 : len( text ) ]
                #endif
            #endif    
        #endif                          
        if self.packet.payload[ 0 ] == 0x01:
            if self.__comment.clock == "":
                self.__comment.clock = clock
            # endif
            if self.__comment.timestamp == 0:
                self.__comment.timestamp     = self.__timestamp
            # endif 
            if self.packet.payload[ 1 ] == 0x01:     # last or single comment
                self.__comment.text        = self.__comment.text + text
                globalvar.commentary.append( self.__comment )
                self.__comment.reset()
            elif self.packet.payload[ 1 ] == 0x00:   # more to come
                self.__comment.text        = self.__comment.text + text
            # endif
        # endif 
        return
    
    def HandleSysSpeed( self ):
        number = self.packet.payload[ 0 ]
        if number == SYS_SPEED.FL_CAR:
            log.info( "System.Speed, car number : %s" % ( self.packet.payload2str( 1 ) ) )
            globalvar.board.setFastestDriverNo( self.packet.car, self.packet.data, self.packet.payload2str( 1 ) )
        elif number == SYS_SPEED.FL_DRIVER:
            log.info( "System.Speed, driver : %s" % ( self.packet.payload2str( 1 ) ) )
            globalvar.board.setFastestDriverName( self.packet.car, self.packet.data, self.packet.payload2str( 1 ) )
        elif number == SYS_SPEED.FL_TIME:
            log.info( "System.Speed, lap time : %s" % ( self.packet.payload2str( 1 ) ) )
            globalvar.board.setFastestDriverLaptime( self.packet.car, self.packet.data, self.packet.payload2str( 1 ) )
        elif number == SYS_SPEED.FL_LAP:
            log.info( "System.Speed, lap number : %s" % ( self.packet.payload2str( 1 ) ) )
            globalvar.board.setFastestDriverLap( self.packet.car, self.packet.data, self.packet.payload2str( 1 ) )
        else:
            globalvar.log.error( "System.Speed (%X) unhandled : %s" % ( number, self.packet.payload2hexstr( 1 ) ) )
        # endif
        return        
    
    def HandleSysTrack( self ):
        log.info( "System.TrackStatus : data = %i payload = %s" % ( self.packet.data, self.packet.payload2str() ) )
        if self.packet.data == 0x01:
            globalvar.TrackStatus.Status = self.packet.payload[ 0 ] - 0x30
        elif self.packet.data == 0x02:
            log.warning( "System.TrackStatus type = %i = payload = %s" % ( self.packet.data, self.packet.payload2str() ) )    
        elif self.packet.data == 0x03:
            log.warning( "System.TrackStatus type = %i = payload = %s" % ( self.packet.data, self.packet.payload2str() ) )    
        elif self.packet.data == 0x04:
            log.warning( "System.TrackStatus type = %i (?? session-finished ?? ) = payload = %s" % ( self.packet.data, self.packet.payload2str() ) )    
        else:
            log.error( "System.TrackStatus unknown : data = %i = payload = %s" % ( self.packet.data, self.packet.payload2str() ) )    
        # endif                    
        return

    def HandleSysTimeStamp( self ):
        self.__timestamp = self.packet.payload2int()
        secs = self.__timestamp % 60
        mins = self.__timestamp // 60
        hours = 0
        if ( mins > 60 ):
            hours = mins // 60
            mins = mins % 60
        # endif
        log.info( "System.TimeStamp : %i = %02i:%02i:%02i" % ( 
                self.__timestamp, hours, mins, secs ) )
        if self.__StoreData:
            if self.keyframe:
                self.keyframe.close()
                self.keyframe = None
            # end if
            directory = os.path.join( self.__keyPath, "F%06i" % ( self.frame ) )
            if not os.path.exists( directory ):
                os.makedirs( directory )
            # end if
            filename = os.path.join( directory, 'keyframe_ts_%04X.bin' % self.__timestamp ) 
            if not os.path.isfile( filename ):               
                self.keyframe = open( filename, 'wb+', 0 )
            # end if
        # end if
        return
    #
    #   
    #
    def HandleSystemPacket( self ):
        if self.packet.type == SYS.EVENT_ID:
            self.HandleSysEventId()
            return
        elif self.packet.type == SYS.KEY_FRAME:
            self.HandleSysKeyFrame()
            return      
        # endif
        if self.__decryption_error > 3:
            return
        elif self.packet.type == SYS.VALID_MARKER:
            log.info( "System.ValidMarker : data = %i, payload = %s" % ( self.packet.data, self.packet.payload2str() ) )
        elif self.packet.type == SYS.COMMENTARY:
            self.HandleSysComment()                   
        elif self.packet.type == SYS.REFRESH_RATE:
            self.__refreshRate = self.packet.payload2int()
            if self.__refreshRate == 0:
                self.__refreshRate  = 1000;
            # end if                                         
            log.warning( "System.RefreshRate data = %i : payload = %i" % ( self.packet.data, self.__refreshRate ) )
        elif self.packet.type == SYS.NOTICE:
            log.info( "System.Notice : data = %i = payload = %s" % ( self.packet.data, self.packet.payload2str() ) )
            globalvar.TrackStatus.Notice = self.packet.payload2str()
        elif self.packet.type == SYS.TIMESTAMP:
            self.HandleSysTimeStamp()
        elif self.packet.type == SYS.WEATHER:
            log.info( "System.Weather : %i" % ( self.packet.car ) )
        elif self.packet.type == SYS.SPEED:
            self.HandleSysSpeed()
        elif self.packet.type == SYS.TRACK_STATUS:
            self.HandleSysTrack()
        elif self.packet.type == SYS.COPYRIGHT:
            log.info( "System.Copyright : %i = %s" % ( self.packet.car, self.packet.payload2str() ) )
            globalvar.TrackStatus.Copyright = self.packet.payload2str()
        else:
            log.error( "Unknown SYSTEM packet data : %s" % ( self.packet.payload2hexstr() ) )
        # endif
        return
            
    #
    #   
    #
    def HandleCarPacket( self ):
        event = globalvar.TrackStatus.Event
        # log.info( "event %i %s" % ( event, {1:"Race",2:"Practice",3:"Qualifiying"}[ event ] ) )
        text = self.packet.payload2str()
        #
        # car packet
        # 
        if self.packet.type == CAR.POSITION_UPDATE:  
            #
            #  pos update
            #
            log.info( "Position update car: %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            
        elif self.packet.type == CAR.RACE_POSITION[ event ]:
            #
            #
            #
            log.info( "Race position car: %i, data: %i, position: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPosition( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.RACE_DRIVER[ event ]:
            #
            #
            #
            log.info( "Driver name car: %i, data: %i, name: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverName( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.DRIVER_NUMBER[ event ]:
            #
            #
            #
            log.info( "Driver number car: %i, data: %i, number: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverNo( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.GAP[ event ]:
            #
            #
            #
            log.info( "Gap: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverGap( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.LAP[ event ]:
            #
            #
            #
            log.info( "Lap: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverLap( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.LAP_TIME[ event ]:
            #
            #
            #
            log.info( "Laptime: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverLaptime( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.INTERVAL[ event ]:
            #
            #
            #
            log.info( "Interval: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverInterval( self.packet.car, self.packet.data, text )
            if self.__decryption_error <= 3 and event == f1TrackStatus.RACE_EVENT:
                globalvar.board.UpdateDriverGap()
            # end if
        elif self.packet.type == CAR.SECTOR_1[ event ]:
            #
            #
            #
            log.info( "Sector-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverSector( self.packet.car, self.packet.data, 0, text )
            if self.__decryption_error <= 3:
                globalvar.board.setDriverSector( self.packet.car, self.packet.data, 1, "" ) 
                globalvar.board.setDriverSector( self.packet.car, self.packet.data, 2, "" )
            # end if
        elif self.packet.type == CAR.SECTOR_2[ event ]:
            #
            #
            #
            log.info( "Sector-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverSector( self.packet.car, self.packet.data, 1, text )
            if self.__decryption_error <= 3:
                globalvar.board.setDriverSector( self.packet.car, self.packet.data, 2, "" )
            # end if
        elif self.packet.type == CAR.SECTOR_3[ event ]:
            #
            #
            #
            log.info( "Sector-3: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverSector( self.packet.car, self.packet.data, 2, text )

        elif self.packet.type == CAR.PIT_LAP_1[ event ]:
            #
            #
            #
            log.info( "Pit-lap-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPitLap( self.packet.car, self.packet.data, 0, text )

        elif self.packet.type == CAR.PIT_LAP_2[ event ]:
            #
            #
            #
            log.info( "Pit-lap-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPitLap( self.packet.car, self.packet.data, 1, text )
            
        elif self.packet.type == CAR.PERIOD_1[ event ]:
            #
            #
            #
            log.info( "Period-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPeriod( self.packet.car, self.packet.data, 0, text )
            
        elif self.packet.type == CAR.PERIOD_2[ event ]:
            #
            #
            #
            log.info( "Period-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPeriod( self.packet.car, self.packet.data, 1, text )
                                            
        elif self.packet.type == CAR.PERIOD_3[ event ]:
            #
            #
            #
            log.info( "Period-3: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.__decryption_error += globalvar.board.setDriverPeriod( self.packet.car, self.packet.data, 2, text )
            
        elif self.packet.type == CAR.POSITION_HISTORY:  # pos history 
            #
            #
            #
            log.warning( "Position history car: %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )

        else:
            #
            #
            #
            log.error( "Unknown CAR packet data : %s" % ( self.packet.payload2hexstr() ) )
        # endif
        if self.__decryption_error > 3:        
            log.error( "DECRYPTION ERROR !!!!!!!!!!!!!" )
            # Clear the data, we need to re-load the stream
            self.__block = ""
            exit()
        # endif     
        return;

    def parse( self, block ):
        self.__stream.Set( block )
        
        while self.__stream.len() and self.__decryption_error <= 3: 
            if 0:            
                hexstr = ""
                cnt = 0
                for c in self.__block:
                    hexstr = hexstr + "%02X " % ( ord( c ) )
                    cnt = cnt + 1
                    if ( cnt > 16 ): 
                        break 
                    # endif
                # next
                log.debug( "Stream data: {%s}" % hexstr )
            # endif                
            self.packet.set( self.__stream )
            if self.packet.length > 2 and self.packet.car == 0 and self.packet.type == SYS.COMMENTARY:             
                if self.packet.payload[2] < 0x20 or self.packet.payload[2] > 0x7E:
                    return
                      
            if self.packet.car == 0:         
                #
                # system packet
                #
                self.HandleSystemPacket()
            else:
                self.HandleCarPacket()
            # endif
        # end while
        return
    
