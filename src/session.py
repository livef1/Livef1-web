#
#   livef1
#
#   src/session.py - session handling
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
import shutil
import socket
import select
import httplib2
import urllib
import urllib2
import Cookie

from src.drivers import GetBoard
from src.status import GetTrackStatus
from src.comment import GetCommentary
from src.comment import F1Text
from src.bytebuffer import ByteBuffer
from src.packet import SYS, EVENT, SYS_SPEED, CAR
from src.packet import F1Packet

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"
 
class F1Session( object ):
    def __init__( self, theApp, log ):    
        self.theApp             = theApp
        self.commentary         = GetCommentary()
        self.board              = GetBoard()
        self.log                = log
        self.packet             = F1Packet()
        self.comment            = F1Text() 
        self.timestamp          = 0
        self.buffer             = ByteBuffer()
        self.decryption_error   = 0
        self.refreshRate        = 100
        self.keyframe           = None      
        self.frame              = 0
        self.error              = 0
        self.eventid            = 0
        self.StoreData          = False
        self.packet.crypto.reset()
        return;
    # end def

    def HandleSysEventId( self ):
        event_sub_type = 0
        if self.packet.length > 0:                     
            event_sub_type = self.packet.payload[ 0 ] 
        if event_sub_type == 2:
            self.log.info( "SYS.EVENT_ID : (str) %s" % ( self.packet.payload.String[ 1: ] ) )
            if self.packet.payload[ 1 ] == 0x5F:
                log.info( "SYS.EVENT_ID : (date) %s" % ( self.packet.payload.String[ 2: ] ) )
                self.eventid        = int( str( self.packet.payload.String[ 2: ] ) )
            else:
                self.eventid        = int( self.packet.payload.String[ 1: ] )
                self.TrackStatus.reset()                    
                self.TrackStatus.Event     = self.packet.data
                self.TrackStatus.EventId   = self.eventid
                self.commentary.reset()
                self.log.info( "SYS.EVENT_ID : %i" % ( self.eventid ) )
                self.packet.crypto.setKey( int( self.obtain_decryption_key(), 16 ) )                        
            # endif
        else:
            self.log.error( "SYS.EVENT_ID unknown sub type %i" % ( event_sub_type ) )
        # endif
        return  
    # end def

    def HandleSysKeyFrame( self ):      
        last    = self.frame 
        number  = self.packet.payload2int()
        self.log.debug( "Current keyframe: %i, requesting keyframe: %i" % ( self.frame, number ) )
        length = 0
        self.packet.crypto.reset()
        if not int( last ) == int( number ):
            """        
                Close the keyframe file, because wher're switching to a new frame  
            """
            if self.keyframe: 
                self.keyframe.close()
                self.keyframe   = None
            # endif            
            # now obtain the key
            self.log.info( "Loading new keyframe" )
            self.frame  = int( number )
            block       = self.obtain_key_frame( self.frame )
            length      = len( block )                          
            self.parse( block )
            self.decryption_error = 0
            self.packet.crypto.reset() 
        else:
            self.log.info( "Stay at current keyframe" )                         
        # endif
        self.log.info( "SYS.KEY_FRAME : %i (%X), requested : %i (%X),  last : %i (%X), block-length %i" % ( 
                                    self.frame, self.frame, number, number, last, last, length ) )
        return        
    # end def
    
    def HandleSysComment( self ):
        clock = ""
        text = self.packet.payload.String[ 2 : ]
        self.log.info( "System.Commentary : %s" % ( text ) )
        if len( text ) > 8:
            if text[ 2 ] == ':': 
                if text[ 5 : 8 ] == ' - ':
                    clock   = text[ 0 : 5 ]
                    text    = text[ 8 : len( text ) ]
                #endif
            #endif    
        #endif                          
        if self.packet.payload[ 0 ] == 0x01:
            if self.comment.clock == "":
                self.comment.clock = clock
            # endif
            if self.comment.timestamp == 0:
                self.comment.timestamp     = self.timestamp
            # endif 
            if self.packet.payload[ 1 ] == 0x01:     # last or single comment
                self.comment.text        = self.comment.text + text
                self.commentary.append( self.comment )
                self.comment.reset()
            elif self.packet.payload[ 1 ] == 0x00:   # more to come
                self.comment.text        = self.comment.text + text
            # endif
        # endif 
        return
    # end def
    
    def HandleSysSpeed( self ):
        number = self.packet.payload[ 0 ]
        text = self.packet.payload.String[ 1 : ]
        if number == SYS_SPEED.FL_CAR:
            self.log.info( "System.Speed, car number : %s" % ( text ) )
            self.board.setFastestDriverNo( self.packet.car, self.packet.data, text )
        elif number == SYS_SPEED.FL_DRIVER:
            self.log.info( "System.Speed, driver : %s" % ( text ) )
            self.board.setFastestDriverName( self.packet.car, self.packet.data, text )
        elif number == SYS_SPEED.FL_TIME:
            self.log.info( "System.Speed, lap time : %s" % ( text ) )
            self.board.setFastestDriverLaptime( self.packet.car, self.packet.data, text )
        elif number == SYS_SPEED.FL_LAP:
            self.log.info( "System.Speed, lap number : %s" % ( text ) )
            self.board.setFastestDriverLap( self.packet.car, self.packet.data, text )
        else:
            self.log.error( "System.Speed (%X) unhandled : %s" % ( number, self.packet.payload.Hex ) )
        # endif
        return        
    # end def
      
    def HandleSysTrack( self ):
        text = self.packet.payload.String
        self.log.info( "System.TrackStatus : data = %i payload = %s" % ( self.packet.data, text ) )
        if self.packet.data == 0x01:
            self.TrackStatus.Status = self.packet.payload[ 0 ] - 0x30
        elif self.packet.data == 0x02:
            self.log.warning( "System.TrackStatus type = %i = payload = %s" % ( self.packet.data, text ) )    
        elif self.packet.data == 0x03:
            self.log.warning( "System.TrackStatus type = %i = payload = %s" % ( self.packet.data, text ) )
        elif self.packet.data == 0x04:
            self.log.warning( "System.TrackStatus type = %i (?? session-finished ?? ) = payload = %s" % ( self.packet.data, text ) )    
        else:
            self.log.error( "System.TrackStatus unknown : data = %i = payload = %s" % ( self.packet.data, text ) )    
        # endif                    
        return
    # end def

    def HandleSysTimeStamp( self ):
        self.timestamp = self.packet.payload2int()
        secs = self.timestamp % 60
        mins = self.timestamp // 60
        hours = 0
        if ( mins > 60 ):
            hours = mins // 60
            mins = mins % 60
        # endif
        self.log.info( "System.TimeStamp : %i = %02i:%02i:%02i" % ( 
                self.timestamp, hours, mins, secs ) )
        return
    # end def
    
    def HandleSystemPacket( self ):
        if self.packet.type == SYS.EVENT_ID:
            self.HandleSysEventId()
            return
        elif self.packet.type == SYS.KEY_FRAME:
            self.HandleSysKeyFrame()
            return      
        # endif
        if self.StoreData or self.decryption_error > 0:
            return
        if self.packet.payload.length:
            self.log.info( "Payload [%s]" % ( self.packet.payload.Hex ) ) 
        if self.packet.type == SYS.VALID_MARKER:
            self.log.info( "System.ValidMarker( data = %i )" % ( self.packet.data ) )
        elif self.packet.type == SYS.COMMENTARY:
            self.HandleSysComment()                   
        elif self.packet.type == SYS.REFRESH_RATE:
            self.refreshRate = self.packet.payload2int()
            if self.refreshRate == 0:
                self.refreshRate  = 1000;
            # end if                                         
            self.log.warning( "System.RefreshRate( data = %i, payload = %i )" % ( self.packet.data, self.refreshRate ) )
        elif self.packet.type == SYS.NOTICE:
            self.log.info( "System.Notice( data = %i, payload = '%s' )" % ( self.packet.data, self.packet.payload.String ) )
            self.TrackStatus.Notice = self.packet.payload.String
        elif self.packet.type == SYS.TIMESTAMP:
            self.HandleSysTimeStamp()
        elif self.packet.type == SYS.WEATHER:
            text = ''
            if self.packet.payload.length:
                text = ", payload='%s'" % ( self.packet.payload.String )
            # end if 
            self.log.info( "System.Weather( data = %i%s )" % ( self.packet.data, text ) )
        elif self.packet.type == SYS.SPEED:
            self.HandleSysSpeed()
        elif self.packet.type == SYS.TRACK_STATUS:
            self.HandleSysTrack()
        elif self.packet.type == SYS.COPYRIGHT:
            self.log.info( "System.Copyright( data = %i, payload = %s )" % ( self.packet.data, self.packet.payload.String ) )
            self.TrackStatus.Copyright = self.packet.payload.String
        else:
            self.log.error( "Unknown SYSTEM packet data : %s" % ( self.packet.payload.Hex ) )
            self.decryption_error += 1
        # endif
        return
    # end def
            
    def HandleCarPacket( self ):
        if self.StoreData:
            return
        event = self.TrackStatus.Event
        # self.log.info( "event %i %s" % ( event, {1:"Race",2:"Practice",3:"Qualifiying"}[ event ] ) )
        text = self.packet.payload.String
        #
        # car packet
        # 
        if self.packet.type == CAR.POSITION_UPDATE:  
            #
            #  pos update
            #
            self.log.info( "Position update car: %i, data: %i" % ( self.packet.car, self.packet.data ) )
            
        elif self.packet.type == CAR.RACE_POSITION[ event ]:
            #
            #
            #
            self.log.info( "Race position car: %i, data: %i, position: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPosition( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.RACE_DRIVER[ event ]:
            #
            #
            #
            self.log.info( "Driver name car: %i, data: %i, name: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverName( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.DRIVER_NUMBER[ event ]:
            #
            #
            #
            self.log.info( "Driver number car: %i, data: %i, number: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverNo( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.GAP[ event ]:
            #
            #
            #
            self.log.info( "Gap: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverGap( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.LAP[ event ]:
            #
            #
            #
            self.log.info( "Lap: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverLap( self.packet.car, self.packet.data, text )
        elif self.packet.type == CAR.LAP_TIME[ event ]:
            #
            #
            #
            self.log.info( "Laptime: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverLaptime( self.packet.car, self.packet.data, text )

        elif self.packet.type == CAR.INTERVAL[ event ]:
            #
            #
            #
            self.log.info( "Interval: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverInterval( self.packet.car, self.packet.data, text )
            if self.decryption_error <= 3 and event == EVENT.RACE_EVENT:
                self.board.UpdateDriverGap()
            # end if
        elif self.packet.type == CAR.SECTOR_1[ event ]:
            #
            #
            #
            self.log.info( "Sector-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverSector( self.packet.car, self.packet.data, 0, text )
            if self.decryption_error <= 3:
                self.board.setDriverSector( self.packet.car, self.packet.data, 1, "" ) 
                self.board.setDriverSector( self.packet.car, self.packet.data, 2, "" )
            # end if
        elif self.packet.type == CAR.SECTOR_2[ event ]:
            #
            #
            #
            self.log.info( "Sector-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverSector( self.packet.car, self.packet.data, 1, text )
            if self.decryption_error <= 3:
                self.board.setDriverSector( self.packet.car, self.packet.data, 2, "" )
            # end if
        elif self.packet.type == CAR.SECTOR_3[ event ]:
            #
            #
            #
            self.log.info( "Sector-3: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverSector( self.packet.car, self.packet.data, 2, text )

        elif self.packet.type == CAR.PIT_LAP_1[ event ]:
            #
            #
            #
            self.log.info( "Pit-lap-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPitLap( self.packet.car, self.packet.data, 0, text )

        elif self.packet.type == CAR.PIT_LAP_2[ event ]:
            #
            #
            #
            self.log.info( "Pit-lap-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPitLap( self.packet.car, self.packet.data, 1, text )
            
        elif self.packet.type == CAR.PERIOD_1[ event ]:
            #
            #
            #
            self.log.info( "Period-1: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPeriod( self.packet.car, self.packet.data, 0, text )
            
        elif self.packet.type == CAR.PERIOD_2[ event ]:
            #
            #
            #
            self.log.info( "Period-2: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPeriod( self.packet.car, self.packet.data, 1, text )
                                            
        elif self.packet.type == CAR.PERIOD_3[ event ]:
            #
            #
            #
            self.log.info( "Period-3: car %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )
            self.decryption_error += self.board.setDriverPeriod( self.packet.car, self.packet.data, 2, text )
            
        elif self.packet.type == CAR.POSITION_HISTORY:  # pos history 
            #
            #
            #
            self.log.warning( "Position history car: %i, data: %i, payload: %s" % ( self.packet.car, self.packet.data, text ) )

        else:
            #
            #
            #
            self.log.error( "Unknown CAR packet data : %s" % ( self.packet.payload2hexstr() ) )
            self.decryption_error += 1
        # endif
        if self.decryption_error > 3:        
            self.log.error( "DECRYPTION ERROR !!!!!!!!!!!!!" )
        # endif     
        return;
    # end def

    def parse( self, block ):
        self.buffer.String = block       
        while len( self.buffer ) and self.decryption_error <= 3: 
            if not self.packet.decode( self.buffer ):
                self.decryption_error += 1
            # end if                 
            if self.packet.length > 2 and self.packet.car == 0 and self.packet.type == SYS.COMMENTARY:             
                if self.packet.payload[2] < 0x20 or self.packet.payload[2] > 0x7E:
                    return
                # end if
            # end if      
            if self.packet.car == 0:         
                #
                # system packet
                #
                self.HandleSystemPacket()
            else:
                self.HandleCarPacket()
            # end if
        # end while
        return
    # end def
     
    def obtain_auth_cookie( self ):
        self.log.info( "Obtaining authentication cookie" )
        return
    # end def
    
    def obtain_key_frame( self, number = 0 ):
        self.log.info( "Obtaining key frame: %i" % ( number ) )
        return
    # end def

    def open( self ):
        return
    # end def

    def close( self ):
        return
    # end def

    #def read( self ):
    #    return
    # end def
    
    def CheckIt( self ):
        return
    # end def

# end class

class f1StreamSession( F1Session ):
    def __init__( self, theApp, log ):
        F1Session.__init__( self, theApp, log )
        self.__username         = self.theApp.config.get( 'registration', 'user' )
        self.__password         = self.theApp.config.get( 'registration', 'passwd' )
        self.log.debug( "user = %s, passwd = %s" % ( self.__username, self.__password ) )
        self.TrackStatus        = GetTrackStatus()
        self.__http             = httplib2.Http()
        self.__cookie           = None
        self.lastTimeStamp      = 0
        self.__timer            = 0
        self.pollCount          = 0
        self.fileindex          = 0
        self.auth_http_host     = self.theApp.config.get( 'host', 'http_addr' )
        self.auth_http_port     = self.theApp.config.getint( 'host', 'http_port' )
        self.data_host          = self.theApp.config.get( 'host', 'data_addr' )
        self.data_port          = self.theApp.config.getint( 'host', 'data_port' )

        self.LOGIN_URL          = self.theApp.config.get( 'urls', 'login_url' )
        self.REGISTER_URL       = self.theApp.config.get( 'urls', 'register_url' )
        self.KEY_URL_BASE       = self.theApp.config.get( 'urls', 'key_url_base' )
        self.KEYFRAME_URL_PREFIX= self.theApp.config.get( 'urls', 'keyframe_url_prefix' )
       
        self.__COOKIE_VALUE     = None
        if self.theApp.config.has_section( 'keyframe' ):
            self.StoreData      = ( self.theApp.config.get( 'keyframe', 'store' ) == "True" )
            self.__keyPath      = self.theApp.config.get( 'keyframe', 'dir' )
        else:
            self.StoreData      = False
            self.__keyPath      = ''                        
        return
    # end def

    def HandleSysEventId( self ):
        """
            This moves keyframe.bin from E000000 folder to actual event id folder. 
        """
        save_event = self.eventid
        F1Session.HandleSysEventId( self )
        if self.StoreData and not save_event == self.eventid:
            # rename folder E000000 -> E<event>
            src_directory = os.path.join( self.__keyPath, "E%06i" % ( 0 ) )
            dest_directory = os.path.join( self.__keyPath, "E%06i" % ( self.TrackStatus.EventId ) ) 
            if not os.path.exists( dest_directory ):
                os.makedirs( dest_directory )
            # end if
            src_directory = os.path.join( src_directory, "keyframe.bin" )
            self.log.debug( "Renaming  %s => %s" % ( src_directory, dest_directory ) )
            os.remove( os.path.join( dest_directory, "keyframe.bin" ) )
            shutil.move( src_directory, dest_directory )           
            os.rmdir( os.path.join( self.__keyPath, "E%06i" % ( 0 ) ) )
        # end if
        return
    # end def          

    def HandleSysTimeStamp( self ):
        # Store the last known timestamp
        self.lastTimeStamp  = self.timestamp
        F1Session.HandleSysTimeStamp( self )
        return
    # end def

    def obtain_auth_cookie( self ):
        F1Session.obtain_auth_cookie( self );
        headers = { "Content-Type": "application/x-www-form-urlencoded" }
        body = { 'email': self.__username, 'password': self.__password }
        url = 'http://%s:%s%s' % ( self.auth_http_host, self.auth_http_port, self.LOGIN_URL )
        self.log.info( "REQ: %s  %s" % ( url, urllib.urlencode( body ) ) ) 
        response, content = self.__http.request( url, 'POST', headers=headers, body=urllib.urlencode(body))
        self.log.debug( "RESP: %s" % ( response ) )
        # self.log.debug( "DATA: %s" % ( content ) )
        if response[ 'status' ] == '200' or response[ 'status' ] == '302':
            try:
                self.__cookie = response[ 'set-cookie' ]
                C = Cookie.BaseCookie( self.__cookie )
                for k, v in C.items():
                    if ( k == "USER" ): 
                        self.__COOKIE_VALUE = v.value
                    # end if
                # end for 
                self.log.debug( "Cookie.USER = %s" % ( self.__COOKIE_VALUE ) )
                return self.__COOKIE_VALUE
            except:
                # Cookie problem
                self.log.debug( "Cookie problem, response data [%s]" % ( response ) )
                # self.log.debug( "Cookie problem, content data [%s]" % ( content ) )
            # end try                                
        # end if
        return ""
    # end def

    def obtain_key_frame( self, number = 0 ):
        F1Session.obtain_key_frame( self, number )        
        outfile = "keyframe.bin"
        if number > 0:
            self.frame = number;
            url = "http://%s:%i" % ( self.auth_http_host, self.auth_http_port )
            url += "%s_%05i.bin" % ( self.KEYFRAME_URL_PREFIX, self.frame )
            outfile = 'keyframe_%05d.bin' % ( self.frame )
        else:
            url = 'http://%s:%s%s.bin' % ( self.auth_http_host, self.auth_http_port, self.KEYFRAME_URL_PREFIX )
            self.frame = number
            self.fileindex          = 0
        # end if
        self.log.info( "REQ: %s" % ( url ) ) 
        response, content = self.__http.request( url, 'GET' )
        self.log.debug( "RESP: %s" % ( response ) )
        # end if            
        if response[ 'status' ] == '200':
            # self.__theApp.hexDebug( "KEYFRAME", content )
            if self.StoreData:
                if self.keyframe:
                    self.keyframe.close()
                # end if
                self.keyframe = None                    
                directory = os.path.join( self.__keyPath, "E%06i" % ( self.TrackStatus.EventId ) )
                if not os.path.exists( directory ):
                    os.makedirs( directory )
                # end if
                filename = os.path.join( directory, outfile )
                if os.path.exists( filename ):
                    os.remove( filename )
                # end if                     
                self.keyframe = open( filename, 'wb+', 0 )
                self.keyframe.write( content )
                self.keyframe.close()
                self.keyframe = None
            # end if
            return content           
        # end if
        return "" 
    # end def

    def obtain_decryption_key( self ):
        url = "http://%s:%s%s%u.asp?auth=%s" % ( self.auth_http_host, self.auth_http_port, self.KEY_URL_BASE, self.eventid, self.__COOKIE_VALUE )
        response, content = self.__http.request( url, 'GET' )
        #self.log.debug( "RESP: %s" % ( response ) )
        self.log.debug( "DATA: %s" % ( content ) )
        if self.StoreData:
            directory = os.path.join( self.__keyPath, "E%06i" % ( self.TrackStatus.EventId ) )
            if not os.path.exists( directory ):
                os.makedirs( directory )
            # end if
            filename = os.path.join( directory, '%s.key' % ( self.eventid ) )
            if os.path.exists( filename ):
                os.remove( filename )
            # end if   
            # end if
            if not os.path.isfile( filename ):
                key = open( filename, 'wb+', 0 )
                key.write( content )
                key.close()
            # end if
        # end if            
        return content
    # end def
        
    def open( self ):
        self.log.debug( "Connecting: %s:%s" % ( self.data_host, self.data_port ) )
        addrlist = socket.getaddrinfo( self.data_host, self.data_port, 0, 0, socket.SOL_TCP )
        for addr in addrlist:
            self.sock = socket.socket( addr[0], addr[1], addr[2] );
            if ( self.sock ):
                self.error = self.sock.connect_ex( addr[ 4 ] );
                self.log.debug( "open.connect_ex: %s" % ( self.error ) )
                self.decryption_error = 0
                if ( self.error == 0 ):
                    self.pollCount = 0
                    return True
                # end if
            # end if
            self.sock.close() 
        # end if
        self.error = -1
        return False
    # end def

    def close( self ):
        self.sock.close()
        self.error = 0
        return 
    # end def

    def read( self ):
        # Map file descriptors to socket objects
        fd_to_socket = { self.sock.fileno(): self.sock, }
        poller = select.poll() 
        poller.register( self.sock, select.POLLIN | select.POLLHUP | select.POLLERR | select.POLLNVAL )
        # self.log.debug( "read->poll( %i )" % 1 )        
        events = poller.poll( 100 )
        for fd, flag in events:
            if flag & select.POLLIN:
                buff = fd_to_socket[ fd ].recv( 512 );
                if buff:
                    """
                        Do we need to store data and do we have data ? 
                    """
                    if self.StoreData and len( buff ):
                        """
                            Is the keyframe file not open?
                        """
                        if not self.keyframe:
                            directory = os.path.join( self.__keyPath, "E%06i" % ( self.eventid ) )
                            if not os.path.exists( directory ):
                                os.makedirs( directory )
                            # end if
                            filename = os.path.join( directory, 'keyframe_seq_%05u.bin' % self.fileindex )
                            if os.path.exists( filename ):
                                os.remove( filename )
                            # end if    
                            self.keyframe = open( filename, 'wb+', 0 )
                            self.fileindex += 1
                        else:
                            self.log.info( "Keyfile : already open" )
                        # end if
                        if len( buff ):
                            """
                                Write the data to the file                        
                            """                    
                            self.keyframe.write( buff )
                        # end if
                    # end if
                    self.parse( buff )
                    self.__timer = 0
                    """
                        Only detect decryption errors when we are not storing the data
                    """
                    if not self.StoreData and self.decryption_error > 3:
                        poller.unregister( self.sock )
                        self.log.info( "Close : Due to decryption error" )
                        self.close()
                        return False
                    # end if
                    self.pollCount = 0
                    return True
                else:
                    # Interpret empty result as closed connection
                    poller.unregister( self.sock )
                    self.log.debug( "Close : #1" )
                    self.close()
                    self.error = -1
                    return False   
                # end if
            elif flag & select.POLLHUP:
                # Client hung up
                poller.unregister( self.sock )
                self.close()
                self.log.debug( "Close : #2" )
            elif flag & select.POLLERR:
                # Error
                poller.unregister( self.sock )
                self.close()
                self.log.debug( "Close : #3" )
            else:
                # something else just ignore
                self.log.debug( "Else : #1" )
            # endif
        # next    
        self.__timer = self.__timer + 1
        # self.log.debug( "Timeout : %i" % self.__timer )
        if self.__timer < 10:   # 10 seconds
            return True
        # endif
        # Timeout ?
        b = bytes( "\x10" ) 
        self.pollCount += 1
        #if ( self.pollCount % 10 ) == 0:
        #    self.board.dump()
        # end if
        if self.pollCount >= 60: # 600 seconds
            self.log.debug( "restart" )
            return False
        # endif
        """
            Send PING to server 
        """
        length = self.sock.send( b )
        # self.log.debug( "Send : %s, length : %i, pollCount %i, RefreshRate %i" % ( b, length, self.pollCount, self.refreshRate ) )
        if length > 0:
            # Reset the timer value.
            self.__timer = 0
            # return true to continue 
            return True
        # end if
        self.log.debug( "restart" )
        return False
    # end def
# end class

class f1FileSession( F1Session ):
    def __init__( self, theApp, log, eventDir ):
        F1Session.__init__( self, theApp, log )
        self.__keyPath          = os.path.join( os.path.dirname( __file__ ), self.theApp.config.get( 'keyframe', 'dir' ) ) 
        self.__keyPath          = os.path.join( self.__keyPath, eventDir )
        self.framepath          = ''
        return 
    # end def

    def HandleSysTimeStamp( self ):
        # Store the last known timestamp
        self.lastTimeStamp  = self.timestamp
        # Update to the next timestamp
        F1Session.HandleSysTimeStamp( self )
        # sleep until the next timestamp
        Sleep( self.timestamp - self.lastTimeStamp )
        return
    # end def

    def Run( self ):
        run     = 1
        while run:
            self.parse( self.obtain_key_frame() )
            if ( self.open() ):
                while ( self.readStream() > 0 ):
                    self.CheckIt()
                    continue
                # end while
                #
                #   Posible to get here from a decryption error, so just recycle the session 
                self.close()
            else:   
                # stop the thread for now
                self.log.error( "Error %s, connecting, try %i of 5" % ( Sess.error, ctries ) )
                run = 0
            # end if  
        # end while
        return
    # end def

    def obtain_auth_cookie( self ):
        F1Session.obtain_auth_cookie( self )
        self.frame  = 0
        # return the cookie value        
        return "COOKIE" 
    # end def

    def obtain_decryption_key( self ):
        # return the descryption KEY
        keyfile = open( os.path.join( self.__keyPath, 'keyframe.key' ), 'r' )
        key = keyfile.read()
        keyfile.close()
        return key
    # end def

    def obtain_key_frame( self, number = 0 ):
        # return the loaded keyframe
        self.framepath = os.path.join( self.__keyPath, "F06i" % ( self.frame ) )
        frame_file = open( os.path.join( framepath, "keyframe_http_%04X.bin" % ( self.timestamp ) ) )
        contents = frame_file.read()
        frame_file.close()
        frame_file  = None        
        return contents 
    # end def
        
    def open( self ):
        if frame_file:
            frame_file.close()
            frame_file = None
        # end if
        self.framepath = os.path.join( self.__keyPath, "F06i" % ( self.frame ) )
        frame_file = open( os.path.join( framepath, "keyframe_ts_%04X.bin" % ( self.timestamp ) ) )
        # open the file
        return
    # end def

    def close( self ):
        # close the file
        if frame_file:
            frame_file.close()
        # end if 
        frame_file  = None        
        return
    # end def

    def read( self ):
        # read the data from the file
        if frame_file: 
            contents = frame_file.read()
            contents = frame_file.read()
            self.parse( buff )
        # end if
        return False
    # end def
# end class
