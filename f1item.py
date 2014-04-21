#
#   livef1
#
#   f1item.py - Storage class for the drivers information 
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
import logging
log  = logging.getLogger('live-f1')

class f1Item( object ):
    def __init__( self, _name, _value = '', _data = 0 ):
        self.__data     = _data
        self.__value    = _value
        self.__name     = _name
        return;
    # end def
    
    def __getData( self ):
        return self.__data
    # end def
        
    def __setData( self, d ):
        self.__data = d
        return         
    # end def

    def __getValue( self ):
        return self.__value
    # end def
        
    def __setValue( self, d ):
        if type( self.__value ) == "<type 'int'>":
            if d.isdigit():             
                self.__value = int( d )
            else:
                self.__value = 0            
            # end if            
        else:             
            self.__value = d
        return         
    # end def

    data    = property( __getData, __setData )
    value   = property( __getValue, __setValue )

    def getHtml( self ):
        if type( self.__value ) == "<type 'int'>":
            return "<td class='%s' id='status_data_%02X'> %i </td>" % ( self.__name, self.__data, self.__value )    
        # end if        
        return "<td class='%s' id='status_data_%02X'> %s </td>" % ( self.__name, self.__data, self.__value )
