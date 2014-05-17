from src.crypt      import F1Crypto
from src.bytebuffer import ByteBuffer
from src.enum       import enum
import logging      # for getLogger()

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

SYS         = enum( 'POSITION_UPDATE',
                    'EVENT_ID', 
                    'KEY_FRAME', 
                    'VALID_MARKER',
                    'COMMENTARY',
                    'REFRESH_RATE',
                    'NOTICE',
                    'TIMESTAMP',
                    'UNKNOWN_8',
                    'WEATHER',
                    'SPEED', 
                    'TRACK_STATUS',
                    'COPYRIGHT',
                    'UNKNOWN_13',
                    'UNKNOWN_14',
                    'POSITION_HISTORY' )

EVENT       = enum( 'no-event', 'RACE_EVENT', 'PRACTICE_EVENT', 'QUALIFYING_EVENT' )

FLAGS       = enum( 'no-flag', 'GREEN_FLAG', 'YELLOW_FLAG', 'SAFETY_CAR_STANDBY', 
                    'SAFETY_CAR_DEPLOYED', 'RED_FLAG', 'LAST_FLAG' )

SYS_SPEED   = enum( 'SPEED_0', 'SPEED_SECTOR1', 'SPEED_SECTOR2', 'SPEED_SECTOR3', 'SPEED_TRAP',
                    'FL_CAR', 'FL_DRIVER', 'FL_TIME', 'FL_LAP' )   

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
   
class F1Packet( object ):
    def __init__( self ):
        self.Clear()
        self.log        = logging.getLogger('live-f1')
        self.crypto     = F1Crypto( self.log )
        return
    # end def 

    def __SwapValueLength( self ):
        tmp             = self.value
        self.value      = self.length
        self.length     = tmp
        return        
    
    def Clear( self ):
        self.type       = 0
        self.car        = 0
        self.type       = 0
        self.length     = 0
        self.data       = 0
        self.payload    = ByteBuffer()
        return;        
    # end def
         
    def decode( self, buffer ):
        if buffer.size() < 2:
            # All data is been read, so clear the buffer.
            buffer.clear()
            return True
        # end if            
        # self.log.debug( "Buffer size %i, index: %i" % ( buffer.length, buffer.index ) )            
        # read the two header bytes
        b1              = buffer.readByte()
        b2              = buffer.readByte()           
        self.car        = ( b1 & 0x1F );
        self.type       =  ( ( b1 & 0xE0 ) >> 5 & 0x7 | ( b2 & 0x1) << 3 );
        self.data       =  ( ( b2 & 0x0E ) >> 1 );
        self.length     =  ( ( b2 & 0xF0 ) >> 4 );
        self.value      =  ( ( b2 & 0xFE ) >> 1 );        
        #self.log.debug( "Header: (%02X,%02X), type: %i, car %i, data: %i, len: %i, value: %s" % ( 
        #                    b1, b2, self.type, self.car, self.data, self.length, self.value ) )
        # clearing the payload buffer
        self.payload.clear()
        decrypt = False                                    
        result  = True
        # set the default for the packet type string
        typeString = "Unhandled packet"
        if self.car == 0:
            if self.type == SYS.EVENT_ID:
                typeString = "SYS.EVENT_ID"
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )
            elif self.type == SYS.KEY_FRAME:
                typeString = "SYS.KEY_FRAME"              
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )
            elif self.type == SYS.VALID_MARKER:
                typeString = "SYS.VALID_MARKER"
                if not self.length == 0:
                    self.log.debug(  "Long valid marker" )
                # end if          
                # read the payload

            elif self.type == SYS.REFRESH_RATE:
                typeString = "SYS.REFRESH_RATE"    
                # read the payload

            elif self.type == SYS.TIMESTAMP:
                typeString = "SYS.TIMESTAMP"
                decrypt         = True
                self.length     = 2
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )         
            elif self.type == SYS.WEATHER:
                typeString = "SYS.WEATHER"
                if self.length < 15:
                    decrypt = True
                    # read the payload
                    self.payload.Bytes = buffer.readBytes( self.length )       
                # end if
            elif self.type == SYS.SPEED:
                typeString = "SYS.SPEED"
                decrypt = True
                self.__SwapValueLength()
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )        
            elif self.type == SYS.TRACK_STATUS:
                typeString = "SYS.TRACK_STATUS"
                decrypt = True
                self.payload.Bytes = buffer.readBytes( self.length )       
            elif self.type == SYS.NOTICE:
                typeString = "SYS.NOTICE"
                self.__SwapValueLength()
                decrypt = True
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )       
            elif self.type == SYS.COPYRIGHT:
                typeString = "SYS.COPYRIGHT"
                self.__SwapValueLength()
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )       
            elif self.type == SYS.COMMENTARY:
                typeString = "SYS.COMMENTARY"
                self.__SwapValueLength()
                # read the payload
                self.payload.Bytes = buffer.readBytes( self.length )       
                decrypt = True                                 
            else:
                # un-handled packet type                
                result = False                                            
            # end if                                            
        else:
            if self.type == SYS.POSITION_HISTORY:
                typeString = "POSITION_HISTORY"
                decrypt = True               
                self.__SwapValueLength()
                if self.length:
                    # read the payload
                    self.payload.Bytes = buffer.readBytes( self.length )                 
                # end if
            elif not self.type == SYS.POSITION_UPDATE:
                #
                #   Depending on the event type car data packets have different 
                #   meaning. See the CAR class for more information
                #
                typeString = "CAR_DATA_PACKET"
                decrypt = True
                if self.length:
                    # read the payload
                    self.payload.Bytes = buffer.readBytes( self.length )
                # end if
            else:
                typeString = "POSITION_UPDATE"                                
            # end if
        # end if

        if decrypt and self.payload and self.length:
            self.crypto.decryptBlock( self.payload ) 
        # end if
        if self.payload.isprint():
            text = '"%s"' % self.payload.String
        else:
            text = '[%s]' % self.payload.Hex
        self.log.debug( "Packet: (%02X,%02X) type: %i (%s), car %i, data: %i, len: %i, value: %s, payload %s" % ( 
                    b1, b2, self.type, typeString, self.car, self.data, self.length, self.value, text ) )
        return result
    # end def 
              
    def payload2int( self, off = 0 ):
        val = 0
        if self.payload:
            shift = 0
            for c in self.payload[ off : self.length ]:
                val |= ( c << shift ) 
                shift = shift + 8
            # next            
        # end if            
        return val
    # end def
# end class
