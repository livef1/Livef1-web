#!/usr/bin/python
#
#   livef1
#
#   livef1.py - Main program file
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
import os, re
import cherrypy
import logging
import ConfigParser
from logging import handlers

from src.reader import StreamReaderThread

from src.status import GetTrackStatus
from src.drivers import GetBoard
from src.comment import GetCommentary

__version__ = "0.1"
__applic__  = "Live F1 Web"
__author__  = "Marc Bertens"

class F1LiveServer( object ):
    def __init__( self, config_file ):
        self.log                = logging.getLogger('live-f1')
        self.TrackStatus        = GetTrackStatus()
        self.board              = GetBoard()
        self.commentary         = GetCommentary()
        self.config             = ConfigParser.RawConfigParser()
        self.config_file        = config_file 
        self.config.read( self.config_file )
        self.openLogFileHandler()
        self.log.info( 'Starting the application' )
        self.RefreshRate        = 5
        self.autoRefresh        = True
        self.loadingKeyframe    = False
        self.interpolateNext    = False
        self.location           = '/'
        self.readerThread       = StreamReaderThread( "live-reader", self )
        return
    # end constructor    
   
    def header( self, title, interval = None ):
        outp = """<!DOCTYPE html><html><head><title>%s</title>""" % ( title )
        if self.autoRefresh and interval:
            outp += "<meta http-equiv='REFRESH' content='%i'>" % ( interval )          
        # end if                     
        outp += """<link rel='stylesheet' type= 'text/css' href='/livef1.css' />
                    <link rel='icon' type='image/ico' href='/images/favicon.ico'>"""
        #outp += "<h2>%s</h2>" % ( title )
        outp += "</head><body><div class='buttons'><ul><span></span>"

        if self.readerThread: 
            if self.readerThread.running == 0:
                outp += "<li><a href='/startreader'>Start reader</a></li>"
            else:
                outp += "<li><a href='/stopreader'>Stop reader</a></li>"                
            # end if                                
        else:
            # self.readerThread not created or destroyed            
            exit() 
        # end if
        outp += "<li><a href='/logging'>Logging</a></li>"
        outp += "<li><a href='/settings'>Settings</a></li>"
        if self.autoRefresh:
            outp += "<li><a href='/refresh?auto=False&location=%s'>Don't Refresh</a></li>" % ( self.location )        
        else:            
            outp += "<li><a href='/refresh?auto=True&location=%s'>Auto Refresh</a></li>" % ( self.location )

        outp += "<li><a href='/comment'>Commentary</a></li>"        

        outp += "<li><a href='/drivers'>Drivers</a></li>"

        outp += "<li><a href='/'>Overview</a></li>"

        outp += "<li><p class='status'>%s (%i)" % ( self.TrackStatus.EventStr, self.TrackStatus.EventId ) 
        outp += "<li><p class='status'>Lap %i of %i" % ( self.TrackStatus.Lap, self.TrackStatus.NrOfLaps )
        outp += "<li><p class='status'>Time left: %s" % ( self.TrackStatus.TimeLeft ) 
        outp += "</ul></div>"
        return outp
    # end def
                                        
    def trailer( self, trail = None ):
        outp = "<div class='trailer'><h3>LiveF1Web: Copyright 2014 by Marc Bertens, all rights reserved"
        if trail:            	   
            outp += ", Timing info: %s</h3></div></body></html>" % ( trail )
        # end if
        return outp
    # end def
        
    def index( self ):
        self.location           = '/'
        yield self.header( "Live F1 Web - Timing", self.readerThread.Interval )
        yield self.board.gethtml( 'contents' )
        #yield self.TrackStatus.getHtml( 'status' )
        yield self.commentary.gethtml( 'comment' ) 
        yield self.trailer( self.TrackStatus.Copyright )
    # end def
    index.exposed = True

    def refresh( self, auto, location ):
        self.autoRefresh = ( auto == 'True' )
        raise cherrypy.HTTPRedirect( location )                 
    # end if     
    refresh.exposed = True
     
    def startreader( self ):
        if self.readerThread: 
            if self.readerThread.running == 0:
                self.config.read( self.config_file )
                self.readerThread       = None
                self.readerThread       = StreamReaderThread( "live-reader", self )
                self.autoRefresh        = True
            # end if
        # end if                     
        raise cherrypy.HTTPRedirect( '/' )                 
    # end def
    startreader.exposed = True 
    
    def stopreader( self ):
        if self.readerThread: 
            if self.readerThread.running == 1:
                self.readerThread.join()
                self.autoRefresh    = False
            # end if
        # end if                                                                        
        raise cherrypy.HTTPRedirect('/' )                 
    # end def
    stopreader.exposed = True 

    def setvalues( self, *args, **kw ):
        logsizes = { 'K': 1024, 'M': 1024 * 1024, 'G': 1024 * 1024 * 1024 }
        #
        #   User/password
        #
        self.config.set( 'registration', 'user',        kw[ 'user' ] )        
        self.config.set( 'registration', 'passwd',      kw[ 'passwd' ] )
        #
        #   Logging
        #
        self.config.set( 'log', 'file',                 kw[ 'logfile' ] )
        self.config.set( 'log', 'dir',                  kw[ 'logdir' ] )
        self.config.set( 'log', 'level',                str( int( kw[ 'loglevel' ] ) * 10 ) )
        self.config.set( 'log', 'size',                 str( int( kw[ 'logsize' ] ) * logsizes[ kw[ 'logsize_id' ] ] ) )
        self.config.set( 'log', 'backup',               kw[ 'logbackup' ] )
        self.config.set( 'log', 'loglines',             kw[ 'loglines' ] )
        #
        #   Host
        #
        self.config.set( 'host', 'http_addr',           kw[ 'httphost' ] )
        self.config.set( 'host', 'http_port',           kw[ 'httpport' ] )
        self.config.set( 'host', 'data_addr',           kw[ 'datahost' ] )
        self.config.set( 'host', 'data_port',           kw[ 'dataport' ] )        
        #
        #   Urls
        # 
        self.config.set( 'urls', 'login_url',           kw[ 'login_url' ] )
        self.config.set( 'urls', 'register_url',        kw[ 'register_url' ] )
        self.config.set( 'urls', 'key_url_base',        kw[ 'key_url_base' ] )
        self.config.set( 'urls', 'keyframe_url_prefix', kw[ 'keyframe_url_prefix' ] )       
        #
        #   Actial save 
        #
        with open( self.config_file, 'wb') as configfile:
            self.config.write( configfile )
        # end with
        #
        #   Now update the log handler
        #
        self.closeLogFileHandler()
        self.openLogFileHandler()
        self.log.info( 'Log file re-opened' )
        raise cherrypy.HTTPRedirect( '/settings' )   
    setvalues.exposed = True 

    def settings( self ):
        yield self.header( "Live F1 Web - Timing" )
        yield "<div class='settings'><h2 class='setHead'>Settings</h2><hr class='setLine'>"
        yield "<form action='setvalues' method='get'><table><tr><td class='setSubTableLabel'>Formula 1 registration</td><td class='setSubTable'><table>"
        
        yield """<tr><td class='setTableFieldLabel'>E-Mail</td>
                    <td class='setTableField'><input type='text' name='user' id='user' value='%s' size='50'></td> 
                 </tr><tr><td class='setTableFieldLabel'>Password</td>
                    <td class='setTableField'><input type='password' name='passwd' id='passwd' value='%s' size='50'></td> 
                 </tr></table></td></tr>""" % ( self.config.get( 'registration', 'user' ), 
                                                self.config.get( 'registration', 'passwd' ) )
                                                
        yield "</table><hr class='setLine'><table><tr><td class='setSubTableLabel'>Logging</td><td class='setSubTable'><table><table>"
        
        yield """<tr><td class='setTableFieldLabel' >Directory</td>
                    <td class='setField' colspan='2' id='logdir'><input type='text' name='logdir' id='logdir' value='%s' size='100'></td>
                 </tr><tr><td class='setTableFieldLabel'>Filename</td>                                              
                    <td class='setField' colspan='2' id='logfile'><input type='text' name='logfile' id='logfile' value='%s' size='50'></td>
                 </tr>""" % (   self.config.get( 'log', 'dir' ), 
                                self.config.get( 'log', 'file' ) )
        logsize = self.config.getint( 'log', 'size' )
        if ( logsize / 1024 ) > 0:
            # more then Kb
            logsize /= 1024
            logfmt = 'K'
            if ( logsize / 1024 ) > 0:
                # more then Mb
                logfmt = 'M'
                logsize /= 1024
                if ( logsize / 1024 ) > 0:
                    # more then Gb
                    logfmt = 'G'
                    logsize /= 1024
                # end if                        
            # end if                             
        # end if                                                    
        yield """<tr><td class='setTableFieldLabel' >Maximum size</td>
                    <td class='setField' id='logsize'><input type='text' name='logsize' 
                                id='logsize' value='%i' size='10'></td>""" % ( logsize )
                                    
        yield """<td class='setFieldAdd' id='logsize_id'><select name='logsize_id'>"""
        logformats = { 'K': 'Kilo bytes', 'M': 'Mega bytes', 'G': 'Giga bytes' }
        for fmt in logformats:
            if fmt == logfmt:
                yield """<option value="%s" selected>%s</option>""" % ( fmt, logformats[ fmt ] )
            else:
                yield """<option value="%s">%s</option>""" % ( fmt, logformats[ fmt ] ) 
        # next         
        yield """</select></td></tr>"""                                    
        yield """<tr><td class='setTableFieldLabel' >Number of backups</td>                                              
                     <td class='setField' colspan='2' id='logbackup'><select name='logbackup'>"""
        logbackup = self.config.getint( 'log', 'backup' )                
        for i in range( 1, 11 ):
            if logbackup == i: 
                yield """<option value="%i" selected>%i</option>""" % ( i, i )
            else: 
                yield """<option value="%i">%i</option>""" % ( i, i )
            # end if 
        # next 
        yield """</select></td></tr><tr><td class='setTableFieldLabel' >Level</td>
                            <td class='setField' colspan='2' id='loglevel'><select name='loglevel'>"""
        loglevel = self.config.getint( 'log', 'level' ) / 10
        loglevels = { 0: 'Disabled', 1: 'Debug', 2: 'Info', 3: 'Warning', 4: 'Error', 5: 'Critical' }                
        for i in loglevels:
            if loglevel == i: 
                yield "<option value='%i' selected>%s</option>" % ( i, loglevels[ i ] )
            else:
                yield "<option value='%i'>%s</option>" % ( i, loglevels[ i ] )
            # end if
        # next             
        maxLogLines = self.config.getint( 'log', 'loglines' )
        yield """</select></td></tr><tr><td class='setTableFieldLabel' >Log lines</td>
                    <td class='setField' colspan='2' id='loglines'><select name='loglines'>"""        
        for i in range( 10, 101, 10 ):
            if maxLogLines == i: 
                yield "<option value='%i' selected>%s</option>" % ( i, i )
            else:
                yield "<option value='%i'>%s</option>" % ( i, i )
            # end if
        # next             
        yield """</select></tr></table></td></td></tr>"""                                    
        
        yield """</table><hr class='setLine'>
                    <table>
                        <tr>
                            <td class='setSubTableLabel'>Host</td>
                            <td class='setSubTable'><table>
                                <table>
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >HTTP host</td>
                                        <td class='setField' id='httphost'><input type='text' name='httphost' id='httphost' value='live-timing.formula1.com' size='87'></td>
                                        <td class='setFieldAdd' id='httpport'><input type='text' name='httpport' id='httpport' value='80' size='5'></td>
                                    </tr>
                                    
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >Stream host</td>
                                        <td class='setField' id='datahost'><input type='text' name='datahost' id='datahost' value='live-timing.lb.formula1.com' size='87'></td>
                                        <td class='setFieldAdd' id='dataport'><input type='text' name='dataport' id='dataport' value='4321' size='5'></td>
                                    </tr>
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >Key frame URL prefix</td>
                                        <td class='setField' colspan='3' id='keyframe_url_prefix'><input type='text' name='keyframe_url_prefix' id='keyframe_url_prefix' value='/keyframe' size='100'></td>
                                    </tr>
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >Login URL</td>
                                        <td class='setField' colspan='3' id='login_url'><input type='text' name='login_url' id='login_url' value='/reg/login' size='100'></td>
                                    </tr>
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >Registration URL</td>
                                        <td class='setField' colspan='3' id='register_url'><input type='text' name='register_url' id='register_url' value='/reg/registration' size='100'></td>
                                    </tr>
                                    <tr>                                                                                                
                                        <td class='setTableFieldLabel' >Key URL prefix</td>
                                        <td class='setField' colspan='3' id='key_url_base'><input type='text' name='key_url_base' id='key_url_base' value='/reg/getkey/' size='100'></td>
                                    </tr>
                                </table>
                            </td>
                        </tr>                                                            
                    </table>                    
                    <hr class='setLine'>Only the logging parameters are real-time updated, others need application restart
                    <input type='submit' name='Save' id='Save'> 
                </form>"""
        yield "</div>"
        yield self.trailer()
        return
    settings.exposed = True 

    def purge( self, dir, pattern ):
        for f in os.listdir( dir ):
    	   if re.search( pattern, f ):
    	       os.remove( os.path.join( dir, f ) )
    	   # end if
        # next     
    # end def    	

    def closeLogFileHandler( self ):
        unclosed_logs = list( self.log.handlers )
        for uFile in unclosed_logs:
            print uFile
            self.log.removeHandler( uFile )
            uFile.flush()
            uFile.close()
        # next 
        return
    # end def    	
        
    def openLogFileHandler( self ):
        directory = os.path.join( os.path.dirname( __file__ ), self.config.get( 'log', 'dir' ) )
        if not os.path.exists( directory ):
            os.makedirs( directory )
        # end if
        # open the log file
        file_log_handler = handlers.RotatingFileHandler( os.path.join( directory, self.config.get( 'log', 'file' ) ), 
                                                        maxBytes=self.config.getint( 'log', 'size' ), 
                                                        backupCount=self.config.getint( 'log', 'backup' ) )
        self.log.addHandler( file_log_handler )
        formatter = logging.Formatter( '%(asctime)s - %(module)s - %(levelname)s - %(message)s' )
        file_log_handler.setFormatter( formatter )
        self.log.setLevel( self.config.getint( 'log', 'level' ) )    
        return
    # end def    	

    def clearlog( self ):
        directory = os.path.join( os.path.dirname( __file__ ), self.config.get( 'log', 'dir' ) )        
        # First close the lof files
        self.closeLogFileHandler()
        # delete them
        self.purge( directory, self.config.get( 'log', 'file' ) + '.*' )
        # re-open the log file
        self.openLogFileHandler()
        self.log.info( 'Log file re-created' )
        raise cherrypy.HTTPRedirect( '/logging' )           
    clearlog.exposed = True 

    def logging( self, page = None ):
        yield self.header( "Live F1 Web - Timing" )
        maxLogLines = self.config.getint( 'log', 'loglines' )
        if page:
            self.logpage = int( page )             
        else:        
            self.logpage = 0
        # end if
        self.loglines = None  
        logfile = os.path.join( os.path.join( os.path.dirname( __file__ ), self.config.get( 'log', 'dir' ) ), self.config.get( 'log', 'file' ) )         
        
        file = open( logfile, 'rb' )
        self.loglines = file.readlines()        
        file.close()
        self.pages = ( len( self.loglines ) / maxLogLines ) + 1
        yield "<div class='settings'><h2 class='setHead'>Logging</h2><hr class='setLine'>"
        yield """<div class='buttons'><ul>"""
        if not self.pages == 0 and self.pages > 1:        
            yield """<li><a href='/logging?page=%i'>Last</a></li>""" % ( self.pages-1 ) 
        else:
            yield """<li><a>Last</a></li>"""                         
        # end if         

        if self.logpage < self.pages-1:
            yield """<li><a href='/logging?page=%i'>Next</a></li>""" % ( self.logpage + 1 )
        else:
            yield """<li><a>Next</a></li>"""                         
        # end if
 
        if self.logpage > 0:
            yield """<li><a href='/logging?page=%i'>Previous</a></li>""" % ( self.logpage - 1 ) 
        else:
            yield """<li><a>Previous</a></li>"""                         
        # end if             

        if self.logpage > 0:        
            yield """<li><a href='/logging?page=0'>First</a></li>"""
        else:
            yield """<li><a>First</a></li>"""                         
        # end if
        yield """<li><a href='/clearlog'>Clear log</a></li>"""
        yield "</ul></div><ul style='list-style-type:none;margin:0px;padding:5px;width:auto;'>"
        if len( self.loglines ): 
            start   = maxLogLines * self.logpage  
            if start >= len( self.loglines ):
                start = len( self.loglines ) - maxLogLines
            # end if            
            end     = min( start + maxLogLines, len( self.loglines ) - 1 ) 
            for i in range( start, end ):
                yield "<li>%s</li>" % ( self.loglines[ i ] )            
            # next         
        # end if    
        yield "</ul></div>"
        yield self.trailer()
        return
    logging.exposed = True 
        
    def drivers( self ):
        self.location           = '/drivers'
        yield self.header( "Live F1 Web - Timing", self.readerThread.Interval ) 
        #self.board.dump()
        yield self.board.gethtml( 'contents_wide' )
        yield self.trailer( self.TrackStatus.Copyright )
    # end def
    drivers.exposed = True

    def comment( self ):
        self.location           = '/comment'
        yield self.header( "Live F1 Web - Timing", self.readerThread.Interval )         
        yield self.commentary.gethtml( 'comment_wide' )
        yield self.trailer( self.TrackStatus.Copyright )
        return
    # end def
    comment.exposed = True
    
    def status( self ):
        self.location           = '/status'
        yield self.header( "Live F1 Web - Timing", self.readerThread.Interval )
        yield self.TrackStatus.getHtml( 'status_wide' )
        yield self.trailer( self.TrackStatus.Copyright )      
    # end def
    status.exposed = True
        
    def hexDebug( self, title, data, length = -1 ):
        hexstr  = ''
        ascii   = ''
        cnt = 0
        idx = 0
        if length != -1:
            if length >= len( data ):
                length = len( data ) - 1
            # endif
            data = data[ 0 : length ]            
        # endif
        for c in data:
            hexstr = hexstr + "%02X " % ( ord( c ) )
            if ord( c ) < 0x20 or ord( c ) > 0x7F: 
                ascii = ascii + '.'
            else:                
                ascii = ascii + c
            # endif                
            cnt = cnt + 1
            if ( cnt == 16 ):
                self.log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )
                hexstr  = ''
                ascii   = ''
                cnt     = 0
                idx     = idx + 16       
            # endif
        # next
        if 0:
            self.log.debug( "%04X: %s | %s" % ( idx, hexstr, ascii ) )                            
        # endif
        return 
    # end def 
# end class

# cherrypy needs an absolute path to deal with static data

theApp        = F1LiveServer( 'userf1.conf' )
# theApp        = F1LiveServer( 'testLiveF1.conf' )
"""
    This is to stop the reader thread
"""      
def StopReaderThread():
    theApp.readerThread.join()
    return
# end if    

StopReaderThread.priority = 10
cherrypy.engine.subscribe( 'stop', StopReaderThread )

cherrypy.quickstart( theApp, '/', config = os.path.join( os.path.join( os.getcwd(), 
                                            os.path.dirname( __file__ ) ), 'livef1.conf' ) )