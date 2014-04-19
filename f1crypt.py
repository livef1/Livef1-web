#
#   Live F1
#
#   f1crypt.py - Crypto module for F1 live stream.
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
class f1Crypto( object ):
    __seed = 1431655765
    def __init__( self, app, newKey = 0 ):
        self.__theApp = app
        self.__key  = newKey
        self.__mask = self.__seed
        self.__theApp.debug( "f1Crypto loaded with key %X" % ( newKey ) )
        return
    # end def
    
    def setKey( self, newKey ): 
        self.__key    = newKey
        self.__mask   = self.__seed
        self.__theApp.debug( "f1Crypto reset with key %X" % ( newKey ) )
    # end def   

    def reset( self ): 
        self.__mask = self.__seed
        self.__theApp.debug( "f1Crypto reset()" )
        return
    # end def
    
    def decryptBlock( self, block ):
        for i in range( len( block ) ):
            block[ i ] = self.decrypt( block[ i ] ) 
        # next
        return block
    # end def
            
    def decrypt( self, b ):
        if ( self.__key == 0 ): 
            return b
        if ( self.__mask & 0x01 ) == 1:
            key = self.__key
        else:
            key = 0
        self.__mask = ( self.__mask >> 1 & 0x7FFFFFFF ^ key );
        return ( b ^ self.__mask & 0xFF );
    # end def
# end class
