#
#   livef1
#
#   f1status.py - Storage classes track status 
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
from src.packet import EVENT
from src.packet import FLAGS  
__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

log  = logging.getLogger('live-f1')

class F1TrackStatus(object):
    statusFlags     = { 1: "Green",     2: "Yellow",    3: "Yellow", 
                        4: "Yellow",    5: "Red flag",  6: "Finished" }
                        
    events          = { 1: "Race",      2: "Practice",  3: "Qualifying" }     
                            
    statusCSS       = { 1: "track_status_normal",       2: "track_status_yellow", 
                        3: "track_status_yellow",       4: "track_status_yellow", 
                        5: "track_status_red",          6: "track_status_finished" }

    def __init__(self):
        self.reset();
        return
    # end def

    def reset( self ):
        self.__Status           = FLAGS.GREEN_FLAG
        self.__NrOfLaps         = 0
        self.__Lap              = 0
        self.__Message          = ""
        self.__Event            = EVENT.RACE_EVENT
        self.__Flag             = FLAGS.GREEN_FLAG
        self.__epoch_time       = 0
        self.__remaining_time   = 0
        self.__event_id         = 0
        self.__copyright        = ""
        self.__notice           = ""
        return;

    def __getStatus( self ):
        return self.__Status
    # end def
        
    def __setStatus( self, val ):
        if ( val < FLAGS.GREEN_FLAG or val > FLAGS.LAST_FLAG ):
            log.warning( "Invalid status set %i" % val )
            return            
        #endif
        self.__Status = val
        return
    # end def
    
    def __getEventStr( self ):
        return self.events[ self.__Event ]            
    
    def __getLap( self ):
        return self.__Lap
    # end def
        
    def __setLap( self, val ):
        self.__Lap = val
        return
    # end def

    def __getNrOfLaps( self ):
        return self.__NrOfLaps
    # end def
        
    def __setNrOfLaps( self, val ):
        self.__NrOfLaps = val
        return
    # end def

    def __getMessage( self ):
        return self.__Message
    # end def
        
    def __setMessage( self, val ):
        self.__Message = val
        return
    # end def

    def __getCopyright( self ):
        return self.__copyright
    # end def
        
    def __setCopyright( self, val ):
        self.__copyright = val
        return
    # end def

    def __getNotice( self ):
        return self.__notice
    # end def
        
    def __setNotice( self, val ):
        self.__notice = val
        return
        
    # end def        
    def __getEvent( self ):
        return self.__Event
    # end def
        
    def __setEvent( self, val ):
        if ( val < EVENT.RACE_EVENT or val > EVENT.QUALIFYING_EVENT ):
            log.warning( "Invalid event set %i" % val )
            return        
        self.__Event = val
        return
    # end def
    
    def __getEventId( self ):
        return self.__event_id
    # end def
        
    def __setEventId( self, val ):
        self.__event_id = val
        return
    # end def

    def __getFlag( self ):
        return self.__Flag
    # end def
        
    def __setFlag( self, val ):
        if ( val < FLAGS.GREEN_FLAG or val > FLAGS.LAST_FLAG ):
            log.warning( "Invalid flag set %i" % val )
            return            
        self.__Flag = val
        return
    # end def

    def getHtml( self, div_tag_name ):
        output = '''<div class="%s" id="%s"><table>''' % ( div_tag_name, self.statusCSS[ self.__Status ] )  
        output = output + '''<tr>
                                <td colspan="4" width="30%%">%s</td>
                                <td width="30%%">%i</td>
                                <td align="right" width="30%%">00:00:00</td>
                             </tr>''' % ( self.events[ self.__Event ], self.__event_id )
        if self.__Event == EVENT.RACE_EVENT:
            output = output + '''<tr>
                                    <td>Lap</td>
                                    <td>%i</td>
                                    <td>of</td>
                                    <td>%i</td>
                                 </tr>''' % ( self.__Lap, self.__NrOfLaps ) 
        # endif    
        return output + '''</table></div>'''
        return """<h2>Status</h2>status-flag: %i = %s<br/>
                    event-type: %i = %s<br/> 
                    message: %s<br/>
                    nr-of-laps: %i<br/>
                    laps: %i<br/>""" % ( self.__Flag, self.statusFlags[ self.__Flag ],
                                        self.__Event, self.events[ self.__Event ],
                                        self.__Message, 
                                        self.__NrOfLaps, 
                                        self.__Lap )  

    def __getTimeLeft( self ):
        return "1:43:23"     
           
    Status      = property( __getStatus,    __setStatus )
    Lap         = property( __getLap,       __setLap )
    NrOfLaps    = property( __getNrOfLaps,  __setNrOfLaps )
    Message     = property( __getMessage,   __setMessage )
    Event       = property( __getEvent,     __setEvent )
    EventId     = property( __getEventId,   __setEventId )
    Flag        = property( __getFlag,      __setFlag )
    Copyright   = property( __getCopyright, __setCopyright )
    Notice      = property( __getNotice,    __setNotice )
    EventStr    = property( __getEventStr )
    TimeLeft    = property( __getTimeLeft )
    
# end class

status  = None  

def GetTrackStatus():
    global status
    if status == None:
        status  = F1TrackStatus()             
    return status 
# end if    
