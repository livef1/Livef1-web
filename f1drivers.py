#
#   livef1
#
#   f1drivers.py - Storage classes for the drivers information for the events 
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
import re
from f1position import f1Position
from f1status import f1TrackStatus
import logging

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

log  = logging.getLogger('live-f1')

def isprint( _str ):
    for x in _str:
        if x < ' ' or x > '~':    
            return False 
        # end if
    # end for
    return True

def isnumber( _str ):
    for x in _str:
        if x == '.':
            continue
        # end if
        if ( x < '0' or x > '9' ):    
            return False 
        # end if
    # end for
    return True
    
def istime( _time ):
    for x in _time:       
        if x == '.' or x == ':':
            continue
        # end if            
        if x < '0' or x > '9':    
            return False 
        # end if
    # end for
    return True
    
def issector( _sect ):
    """
        This is just a fix, because now the sector times are no longer provided.
        via the free live timing interface.  
    """
    if _sect == '\xE2\x97\x8F':
        return True
    # end if
    return isnumber( _sect )

class f1Board( object ):
    def __init__( self ):
        self.__cars = []
        self.__fastest = f1Position()
        # create 32 cars 
        self.__maxCars = 0
        self.currentLap = 0
        self.Event      = 1
        self.__index    = []
        for i in range( 32 ):
            self.__cars.append( f1Position() )
            self.__index.append( [ 0, 0 ] )
        return
       
    def updateMaxCars( self, car ):
        if car > self.__maxCars:
            self.__maxCars = car
        log.info( "max CARS %i" % self.__maxCars ) 
        self.UpdateTable()
        # end if
        return 
       
    def setDriverNo( self, car, data, number ):
        if not number:
            return 0
        if number.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setNumber( data, number )
            return 0      
        log.error( "setDriverNo not a number [%s]" % ( number ))                   
        return 1

    def setDriverPosition( self, car, data, number ):
        if not number:
            return 0        
        if number.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setPosition( data, number )
            log.info( "LAP setting position %i for car %i" % ( int( number ), car ) )
            self.__index[ int( number ) ] = [ car, int( number ) ]
            return 0 
        log.error( "setDriverPosition not a number [%s]" % ( number ))                          
        return 1
        
    def setDriverName( self, car, data, name ):
        if not name:
            return 0
        if isprint( name ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setName( data, name )
            return 0
        log.error( "setDriverName not a printable string [%s]" % ( name ))                          
        return 1
    
    def setDriverInterval( self, car, data, intr ):
        if not intr:
            return 0
        if isprint( intr ):
            self.updateMaxCars( car )
            if self.Event == 1:
                if car == 1:    # pole position
                    self.__cars[ car-1 ].setInterval( data, '0' )
                    self.__cars[ car-1 ].setLap( data, int( intr ) )
                    self.currentLap = int( intr )                    
                else:
                    self.__cars[ car-1 ].setInterval( data, intr )
                # endif
            else:
                self.__cars[ car-1 ].setInterval( data, intr )                                            
            # end if
            return 0  
        log.error( "setDriverInterval not a number string [%s]" % ( intr ))                         
        return 1       

    def setDriverGap( self, car, data, gap ):
        if not gap:
            return 0
        if isprint( gap ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setGap( data, gap )
            self.UpdateTable()        
            return 0
        log.error( "setDriverGap not a number string [%s]" % ( gap ))                 
        return 1                    

    def setDriverLaptime( self, car, data, laptime ):
        if not laptime:
            return 0
        if isprint( laptime ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setLaptime( data, laptime )        
            return 0
        log.error( "setDriverLaptime not a time string [%s]" % ( laptime ) )        
        return 1        

    def setDriverSector( self, car, data, sect, secttime ):
        if not secttime:
            return 0
        if issector( secttime ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setSector( sect, data, secttime )        
            return 0
        log.error( "setDriverSector not a sector string [%s]" % ( secttime ) )        
        return 1        
        
    def setDriverPitLap( self, car, data, pit, secttime ):
        if not secttime:
            return 0
        self.updateMaxCars( car )
        self.__cars[ car-1 ].setPitLap( pit, data, secttime )        
        return 0   
        
    def setDriverPeriod( self, car, data, period, time ):
        if not time:
            return 0
        if istime( time ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setPeriod( data, period, time )        
            return 0
        log.error( "setDriverPeriod not a sector string [%s]" % ( time ) )            
        return 1        
        
    def setDriverLap( self, car, data, lap ):
        if not lap:
            return 0
        if lap.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setLap( data, lap )        
            return 0
        log.error( "setDriverLap not a number [%s]" % ( lap ) )     
        return 1    
        
    def setFastestDriverNo( self, car, data, number ):
        self.updateMaxCars( car )
        self.__fastest.setNumber( data, number ) 
        return 0
        
    def setFastestDriverName( self, car, data, name ):
        self.updateMaxCars( car )
        self.__fastest.setName( data, name )        
        return 0
        
    def setFastestDriverLaptime( self, car, data, time ):
        self.updateMaxCars( car )
        self.__fastest.setLaptime( data, time )        
        return 0      
        
    def setFastestDriverLap( self, car, data, lap ):
        self.updateMaxCars( car )
        self.__fastest.setLap( data, lap )        
        return 0      
        
    def UpdateDriverGap( self ):
        return

    def ToSecs( self, _time ):
        if _time:   
            times = map( int, re.split( r"[:.]", _time ) )
            times[ 2 ] /= 100
            return float( (times[ 0 ] * 60) + times[ 1 ] + (times[ 2 ] / 1000.) )
        return 0.0

    def UpdateTable( self ):
        #log.info( "Update Table LAP" )
        """
            All this is fussy-logic to restore the items the live timing interface no longer supplies 
        """
        gap = 0.0
        behind = 0
        prev = None
        pole = None
        for car, pos in self.__index:
            if not car == 0:
                if pos == 1:
                    pole    = car - 1
                # end if      
                if not prev == None:
                    prevrec = self.__cars[ prev ] 
                else:
                    prevrec = None                                                      
                #log.info( "Update LAP car %i, pos %i, name: %s" % ( car, pos, self.__cars[ car-1 ].getName().value ) )
                curr_rec = self.__cars[ car-1 ] 
                value = curr_rec.getInterval()                 
                if not value.value == '' and not 'L' in value.value:                
                    gap += float( value.value )
                else:
                    behind += 1
                    if not prevrec == None:
                        gap = ( self.ToSecs( prevrec.getLaptime().value ) * behind ) + 1
                    else:
                        gap = ( self.ToSecs( self.__cars[ pole ].getLaptime().value ) * behind ) + 1
                    # end if
                # end if                                                                                         
                curr_rec.setGap( value.data, "%.1f" % gap )                    
                # end if
                if not prevrec == None:
                    prevrec = self.__cars[ prev ] 
                    value = prevrec.getLap()
                    if "L" in curr_rec.getInterval().value:
                        tmp = ''
                        for x in curr_rec.getInterval().value:
                            if x.isdigit():
                                tmp += x
                            # end if                              
                        # end for
                        if tmp.isdigit():   
                            tmp = int( tmp )                         
                            curr_rec.setLap( 0, str( int(value.value) - tmp ) )                
                        # end if
                    else:
                        curr_rec.setLap( 0, value.value )
                    # end if                        
                # end if    
                prev = car-1                                               
            # end if        
        # end for
        return
        
    def dump( self ):
        log.info( "---------------------------------------------" )
        log.info( "maxCars : %i" % self.__maxCars ) 
        for x in range( self.__maxCars ):
            for y in range( self.__maxCars ):
                item = self.__cars[ y ]
                if item.getPosition().value:
                    if int( item.getPosition().value ) == x:
                        line = "cars: nr: %-3s, pos: %-3s, name: %-13s" % ( item.getNumber().value, 
                                                    item.getPosition().value, item.getName().value ) 
                        if ( item.getLaptime().value ):
                            line = line + ", time: %s" % item.getLaptime().value  
                        if ( item.getInterval().value ):
                            line = line + ", int: %s" % item.getInterval().value     
                        if ( item.getGap().value ):
                            line = line + ", gap: %s" % item.getGap().value
                        if ( item.getLap().value ):
                            line = line + ", lap: %2s" % item.getLap().value
                        if ( item.getPitLap( 0 ).value ):
                            line = line + ", pit: (%s,%s)" % ( item.getPitLap(0).value, item.getPitLap(1).value )
                        #if ( item.getSector( 0 ).value ):
                        #    line = line + ", sect: (%s,%s,%s)" % ( item.getSector( 0 ).value,
                        #                                item.getSector( 1 ).value, item.getSector( 2 ).value );
                        if ( item.getPeriod( 0 ).value ):
                            line = line + ", per: (%s,%s,%s)" % ( item.getPeriod( 0 ).value,
                                                        item.getPeriod( 1 ).value, item.getPeriod( 2 ).value );
                        log.info( line )
                    # end if
                # end if
            # end for
        # end for
        log.info( "fastest: nr: %-3s, name: %-13s, lap: %s, time: %s" % (
                        self.__fastest.getNumber().value,
                        self.__fastest.getName().value,
                        self.__fastest.getLap().value,
                        self.__fastest.getLaptime().value ) )
        log.info( "---------------------------------------------" )        
        return
       
                  
    def gethtml( self, div_tag_name ):
        output = '''<div class="%s"><table border="0" ><thead>
			         <th class="car_position" id="head_color">Pos.</th>
			         <th class="driver_number" id="head_color">Nr.</th>
			         <th class="driver_name" id="head_color">Driver</th>''' % ( div_tag_name )
        if globalvar.TrackStatus.Event == f1TrackStatus.RACE_EVENT:
            output = output + '''<th class="laptime" id="head_color">Lap Time</th>
                                 <th class="interval" id="head_color">Int</th>
                                 <th class="gap" id="head_color">Gap</th>
			                     <th class="sector1" id="head_color">Sec #1</th>
			                     <th class="sector1" id="head_color">Sec #2</th>
			                     <th class="sector1" id="head_color">Sec #3</th>
    		                     <th class="driver_lap" id="head_color">Lap</th>'''
        elif globalvar.TrackStatus.Event == f1TrackStatus.PRACTICE_EVENT:
            output = output + '''<th class="laptime" id="head_color">Lap Time</th>
			                     <th class="sector1" id="head_color">Sec #1</th>
			                     <th class="sector1" id="head_color">Sec #2</th>
			                     <th class="sector1" id="head_color">Sec #3</th>		                     
    		                     <th class="driver_lap" id="head_color">Lap</th>'''
        elif globalvar.TrackStatus.Event == f1TrackStatus.QUALIFYING_EVENT:
            output = output + '''<th class="q1" id="head_color">Q1</th>
                                 <th class="q2" id="head_color">Q2</th>
                                 <th class="q3" id="head_color">Q3</th>
			                     <th class="sector1" id="head_color">Sec #1</th>
			                     <th class="sector2" id="head_color">Sec #2</th>
			                     <th class="sector3" id="head_color">Sec #3</th>
    		                     <th class="driver_lap" id="head_color">Lap</th>'''
        else: 
            output = output + '''UNKNOWN EVENT TYPE !!!! %i''' % ( globalvar.TrackStatus.EventType )
        #endif
        output = output + "</thead><tbody>"            
        # log.info( "cars : %s" % ( cnt ) ) 
        for pos in range( 1, self.__maxCars ):
            for item in self.__cars:
                if int( item.getPosition().value ) == pos:
                    output = output + item.gethtml( globalvar.TrackStatus.Event ) 
                # endif
            # next
        # next
        output = output + """</tbody></table>"""
        if globalvar.TrackStatus.Event == f1TrackStatus.RACE_EVENT:
            output = output + self.__fastest.getHtmlFastest()
            output = output + """</tbody></table></div>"""
        # endif                  
        output = output + "</div>"   
        return output