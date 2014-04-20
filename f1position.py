#
#   livef1
#
#   f1position.py - Storage class for the driver information for the events 
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
from f1item import f1Item
from f1status import f1TrackStatus
import logging

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

log  = logging.getLogger('live-f1')

class f1Position( object ):
    def __init__( self ):
        self.reset()
        return
    # end def

    def reset( self ):
        self.__number     = f1Item()
        self.__name       = f1Item()
        self.__interval   = f1Item()
        self.__laptime    = f1Item()
        self.__sector     = [ f1Item(), f1Item(), f1Item() ]
        self.__lap        = f1Item()
        self.__gap        = f1Item()
        self.__position   = f1Item()
        self.__pitLap     = [ f1Item(), f1Item(), f1Item() ]
        self.__period     = [ f1Item(), f1Item(), f1Item() ]
        return 
    # end def

    def setNumber( self, data, number ):
        self.__number.data  = data  
        self.__number.value = number
        return
        
    def getNumber( self ):
        return self.__number
    # end def
    
    def setPosition( self, data, number ):
        self.__position.data  = data  
        self.__position.value = number
        return
    # end def
        
    def getPosition( self ):
        return self.__position   
    # end def
        
    def setName( self, data, name ):
        self.__name.data  = data  
        self.__name.value = name
        return
    # end def
    
    def getName( self ):
        return self.__name
    # end def
    
    def setInterval( self, data, interval ):
        self.__interval.data  = data  
        self.__interval.value = interval
        return
    # end def

    def getInterval( self ):
        return self.__interval
    # end def
        
    def setGap( self, data, gap ):
        self.__gap.data  = data  
        self.__gap.value = gap
        return
    # end def
        
    def getGap( self ):
        return self.__gap
    # end def

    def setLap( self, data, gap ):
        self.__lap.data  = data  
        self.__lap.value = gap
        return
    # end def
        
    def getLap( self ):
        return self.__lap
    # end def
    
    def setLaptime( self, data, lap ):
        self.__laptime.data  = data  
        self.__laptime.value = lap
        return
    # end def

    def getLaptime( self ):
        return self.__laptime
    # end def

    def setSector( self, sect, data, info ):
        self.__sector[ sect ].data = data
        self.__sector[ sect ].value = info
        return
    # end def
        
    def getSector( self, sect ):
        return self.__sector[ sect ]
    # end def


    def setPitLap( self, pit, data, info ):
        self.__pitLap[ pit ].data = data
        self.__pitLap[ pit ].value = info
        return
    # end def
        
    def getPitLap( self, pit ):
        return self.__pitLap[ pit ]
    # end def

    def setPeriod( self, data, period, time ):
        self.__period[ period ].data = data
        self.__period[ period ].value = time
        return;        
    # end def

    def getPeriod( self, period ):
        return self.__period[ period ]
    # end def

    def isValid( self, mode = 0 ):
        if ( self.__position.value > "0" and self.__number.value > "0" and 
                    self.__name.value and self.__laptime.value > "0" ):
            if mode == 9:
                return True
            #endif
             
        #endif
        return False
    # end def

    def gethtml( self, event ):
        output = '''<tr><td class="car_position" id="status_data_%02X">%s</td> 
                        <td class="driver_number" id="status_data_%02X">%s</td>
                        <td class="driver_name" id="status_data_%02X">%s</td>''' % (      
                           self.__position.data,    self.__position.value,   
                           self.__number.data,      self.__number.value,     
                           self.__name.data,        self.__name.value )      
        if event == f1TrackStatus.RACE_EVENT:
            output = output + '''<td class="laptime"  id="status_data_%02X">%s</td>
                                 <th class="interval" id="status_data_%02X">%s</th>
                                 <th class="gap"      id="status_data_%02X">%s</th>
                                 <td class="sector1" id="status_data_%02X">%s</td>
                                 <td class="sector2" id="status_data_%02X">%s</td>
                                 <td class="sector3" id="status_data_%02X">%s</td>
                                 <td class="driver_lap" id="status_data_%02X">%s</td>''' % (    
                                    self.__laptime.data,        self.__laptime.value,
                                    self.__interval.data,       self.__interval.value,
                                    self.__gap.data,            self.__gap.value,                                                                                  
                                    self.__sector[ 0 ].data,    self.__sector[ 0 ].value,  
                                    self.__sector[ 1 ].data,    self.__sector[ 1 ].value,  
                                    self.__sector[ 2 ].data,    self.__sector[ 2 ].value,  
                                    self.__lap.data,            self.__lap.value )   
        elif event == f1TrackStatus.PRACTICE_EVENT:
            output = output + '''<td class="laptime" id="status_data_%02X">%s</td>
                                 <td class="sector1" id="status_data_%02X">%s</td>
                                 <td class="sector2" id="status_data_%02X">%s</td>
                                 <td class="sector3" id="status_data_%02X">%s</td>
                                 <td class="driver_lap" id="status_data_%02X">%s</td>''' % (    
                                    self.__laptime.data,        self.__laptime.value,    
                                    self.__sector[ 0 ].data,    self.__sector[ 0 ].value,  
                                    self.__sector[ 1 ].data,    self.__sector[ 1 ].value,  
                                    self.__sector[ 2 ].data,    self.__sector[ 2 ].value,  
                                    self.__lap.data,            self.__lap.value )   
        elif event == f1TrackStatus.QUALIFYING_EVENT: 
            output = output + '''<td class="q1" id="status_data_%02X">%s</td>
                                 <td class="q2" id="status_data_%02X">%s</td>
                                 <td class="q3" id="status_data_%02X">%s</td>
                                 <td class="sector1" id="status_data_%02X">%s</td>
                                 <td class="sector2" id="status_data_%02X">%s</td>
                                 <td class="sector3" id="status_data_%02X">%s</td>
                                 <td class="driver_lap" id="status_data_%02X">%s</td>''' % (
                                    self.__period[ 0 ].data,    self.__period[ 0 ].value,
                                    self.__period[ 1 ].data,    self.__period[ 1 ].value,
                                    self.__period[ 2 ].data,    self.__period[ 2 ].value,
                                    self.__sector[ 0 ].data,    self.__sector[ 0 ].value,
                                    self.__sector[ 1 ].data,    self.__sector[ 1 ].value,
                                    self.__sector[ 2 ].data,    self.__sector[ 2 ].value,
                                    self.__lap.data,            self.__lap.value )
        # endif
        output = output + "</tr>"                                
        return output
    # end def
