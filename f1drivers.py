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
import string
import globalvar
#from f1item import f1Item
from f1position import f1Position
from f1status import f1TrackStatus
import logging
log  = logging.getLogger('live-f1')

def isprint( _str ):
    for x in _str:
        if ord(x) < 0x20 or ord(x) > 0x7F:    
            return False 
        # end if
    # end for
    return True

def isnumber( _str ):
    for x in _str:
        if ( ord( x ) < 0x30 or ord( x ) > 0x39 and not x == '.' ):    
            return False 
        # end if
    # end for
    return True
    
def istime( _time ):
    for x in _time:
        i = ord( x )        
        if ( ( i < 0x30 or i > 0x39 ) and not x == '.' and not x == ':' ):    
            return False 
        # end if
    # end for
    return True
    
def issector( _sect ):
    if _sect == '\xE2\x97\x8F':
        return True
    # end if
    for x in _sect:
        i = ord( x )        
        if ( ( i < 0x30 or i > 0x39 ) and not x == '.' and not x == ':' ):    
            return False 
        # end if
    # end for
    return True

class f1Board( object ):
    def __init__( self ):
        self.__cars = []
        self.__fastest = f1Position()
        # create 32 cars 
        self.__maxCars = 0
        for i in range( 32 ):
            self.__cars.append( f1Position() )
        return
       
    def updateMaxCars( self, car ):
        if car > self.__maxCars:
            self.__maxCars = car
        log.info( "max CARS %i" % self.__maxCars ) 
        # end if
        return 
       
    def setDriverNo( self, car, data, number ):
        if not number:
            return True
        if number.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setNumber( data, number )
            return True      
        log.error( "setDriverNo not a number [%s]" % ( number ))                   
        return False

    def setDriverPosition( self, car, data, number ):
        if not number:
            return True        
        if number.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setPosition( data, number )
            return True 
        log.error( "setDriverPosition not a number [%s]" % ( number ))                          
        return False
        
    def setDriverName( self, car, data, name ):
        if isprint( name ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setName( data, name )
            return True
        log.error( "setDriverName not a printable string [%s]" % ( name ))                          
        return False
    
    def setDriverInterval( self, car, data, interval ):
        if isnumber( interval ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setInterval( data, interval )
            return True  
        log.error( "setDriverInterval not a number string [%s]" % ( interval ))                         
        return False       

    def setDriverGap( self, car, data, gap ):
        if isnumber( interval ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setGap( data, gap )        
            return True
        log.error( "setDriverGap not a number string [%s]" % ( gap ))                 
        return False                    

    def setDriverLaptime( self, car, data, laptime ):
        if istime( laptime ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setLaptime( data, laptime )        
            return True
        log.error( "setDriverLaptime not a time string [%s]" % ( laptime ) )        
        return False        

    def setDriverSector( self, car, data, sect, secttime ):
        if issector( secttime ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setSector( sect, data, secttime )        
            return True
        log.error( "setDriverSector not a sector string [%s]" % ( secttime ) )        
        return False        
        
    def setDriverPitLap( self, car, data, pit, secttime ):
        self.updateMaxCars( car )
        self.__cars[ car-1 ].setPitLap( pit, data, secttime )        
        return True   
        
    def setDriverPeriod( self, car, data, period, time ):
        if istime( time ):
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setPeriod( data, period, time )        
            return True
        log.error( "setDriverPeriod not a sector string [%s]" % ( time ) )            
        return False        
        
    def setDriverLap( self, car, data, lap ):
        if not lap:
            return True
        if lap.isdigit():
            self.updateMaxCars( car )
            self.__cars[ car-1 ].setLap( data, lap )        
            return True
        log.error( "setDriverLap not a number [%s]" % ( lap ) )     
        return False    
        
    def setFastestDriverNo( self, car, data, number ):
        self.updateMaxCars( car )
        self.__fastest.setNumber( data, number ) 
        return True
        
    def setFastestDriverName( self, car, data, name ):
        self.updateMaxCars( car )
        self.__fastest.setName( data, name )        
        return True
        
    def setFastestDriverLaptime( self, car, data, time ):
        self.updateMaxCars( car )
        self.__fastest.setLaptime( data, time )        
        return True      
        
    def setFastestDriverLap( self, car, data, lap ):
        self.updateMaxCars( car )
        self.__fastest.setLap( data, lap )        
        return True      
        
    def dump( self ):
        log.info( "---------------------------------------------" )
        for item in self.__cars:
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
        # next
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
        for pos in range( self.__maxCars ):
            for item in self.__cars:
                if str( item.getPosition().value ) == str( pos ):
                    output = output + item.gethtml( globalvar.TrackStatus.Event ) 
                # endif
            # next
        # next
        output = output + """</tbody></table>"""
        if globalvar.TrackStatus.Event == f1TrackStatus.RACE_EVENT:
            output = output + """<div class="fastestlap"><table border="0" ><thead>
					<th class="driver_number" id="head_color">Nr.</th>
					<th class="driver_name" id="head_color">Driver</th>
					<th class="driver_lap" id="head_color" >On lap</th>
					<th class="laptime" id="head_color" width="180" >Lap Time</th>
				</thead>
				<tbody>""" 
            if self.__fastest.isValid( 9 ):
                output = output + """<tr>
						      <td class="driver_number" >%s</td>
						      <td class="driver_name" >%s</td>
						      <td class="driver_lap" align='right'>%s</td>
						      <td class="laptime" align='right'>%s</td>
					       </tr>""" % (   self.__fastest.getNumber().value, 
		                                  self.__fastest.getName().value, 
		                                  self.__fastest.getLap().value, 
		                                  self.__fastest.getLaptime().value )
            # endif					
            output = output + """</tbody></table></div>"""
        # endif                  
        output = output + "</div>"   
        return output