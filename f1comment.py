#
#   livef1
#
#   f1comment.py - classes to store the live F1 comments
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
import time
import datetime
import globalvar
import logging

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

log  = logging.getLogger('live-f1')

class f1text( object ):
    def __init__( self, ts = 0, c = '', t = '' ):
        self.timestamp   = ts
        self.clock       = c
        self.text        = t
        return

    def reset( self ):
        self.timestamp   = 0
        self.clock       = ""
        self.text        = ""  
        return
                
class f1commentary( object ):  
    def __init__( self ):
        self.lines = []
        return 

    def reset( self ):
        self.lines = []
        return
              
    def gethtml( self, div_tag_name ):
        output = "" 
        for elem in self.lines:
            if elem.clock:
                sep = "-"
            else:
                sep = ""
            #endif
            output = "<tr valign='top'><td>%s</td><td>%s</td><td>%s</td></tr>" % ( 
                                            elem.clock, sep, elem.text ) + output
        return """<div class="%s"><table>%s</table></div>""" % ( div_tag_name, output )
        
    def append( self, new ):
        #log.info( "Commentary.time : %i" % ( new.timestamp ) )
        #log.info( "Commentary.text : %s" % ( new.text ) )
        if not new.clock:
            secs = new.timestamp % 60
            mins = new.timestamp // 60
            hours = 0
            if ( mins > 60 ):
                hours = mins // 60
                mins = mins % 60
            # endif
            # add time stamp
            new.clock = "%02i:%02i" % ( hours, mins ) 
        self.lines.append( f1text( new.timestamp, new.clock, new.text ) )
        return
    
    def dump( self ):
        for elem in self.lines:        
            log.info( "Commentary : %s" % ( elem.text ) )
        # next
        return         
        