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
    def __init__( self ):
        self.__data = 0
        self.__value = ""
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
        self.__value = d
        return         
    # end def

    data    = property( __getData, __setData )
    value   = property( __getValue, __setValue )
