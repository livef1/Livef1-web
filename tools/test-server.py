#!/usr/bin/env python 
import os
import cherrypy
import Cookie
import logging
import ConfigParser
from logging import handlers
from stream.server import StreamServerThread

users = {   'mbertens@xs4all.nl':   '5701mb',
            'livef1@pe2mbs.nl':     '123456' }

class F1LiveServer( object ):
    def __init__( self ):
        self.log    = logging.getLogger( 'test-server' )               
        self.config = ConfigParser.RawConfigParser()
        self.config.read( 'test-server-user.conf' )
        directory = os.path.join( os.path.dirname( __file__ ), self.config.get( 'log', 'dir' ) )
        if not os.path.exists( directory ):
            os.makedirs( directory )
        # end if
        file_log_handler = handlers.RotatingFileHandler( os.path.join( directory, self.config.get( 'log', 'file' ) ), 
                                                        maxBytes=self.config.getint( 'log', 'size' ), 
                                                        backupCount=self.config.getint( 'log', 'backup' ) )

        self.log.addHandler( file_log_handler )
        # nice output format
        formatter = logging.Formatter( '%(asctime)s - %(module)s - %(levelname)s - %(message)s' )
        file_log_handler.setFormatter( formatter )
        self.log.setLevel( self.config.getint( 'log', 'level' ) )
        self.__keyDirectory = self.config.get( 'keyframe', 'dir' )           
        self.log.info( 'Starting the application' )
        self.stream = None        
        return
    # end constructor    
    
    def header( self, title, refresh = None ):
        head = ''
        if refresh:
            head = "<meta http-equiv='refresh' content='%i'>" % int( refresh )        
        # end if
        return "<!DOCTYPE html><html><head><title>%s</title>%s</head><body><h1><a href='/'>%s</a></h1>" % ( title, head, title )

    def trailer( self ):
        return "</body></html>"    
    
    def index( self, *args, **kw ):
        yield self.header( 'Test-Server' )
        self.log.debug( repr( dict( args = args, kw = kw ) ) )
        yield '<ul>'
        for file in os.listdir( self.__keyDirectory ):
            yield '<li><a href="/show?folder=%s">%s</a></li>' % ( file, file )
        # next 
        yield '</ul>'
        yield self.trailer()
        return  
    # end def
    index.exposed = True
    """
        Show event folder 
    """
    def show( self, folder, *args, **kw ):
        yield self.header( 'Test-Server' )
        self.log.debug( repr( dict( args = args, kw = kw ) ) )
        yield "<div class='buttons'><ul>"
        if self.stream:
            self.log.debug( "folder : %s" % ( folder ) )                         
            self.log.debug( "event : %s" % ( self.stream.event ) )
            if not self.stream.event == folder:
                raise cherrypy.HTTPRedirect('/')
            # end if
            yield """<li><a href='/stop?folder=%s'>STOP</a></li>
                     <li><a href='/status?folder=%s'>STATUS</a></li>""" % ( folder, folder )         
        else:
            yield "<li><a href='/start?folder=%s'>START</a></li>" % ( folder )
        # end if 
        yield "</ul></div>"
        folder = os.path.join( self.__keyDirectory, folder )
        for file in os.listdir( folder ):      
            yield '<li>%s</li>' % ( file )
        # next  
        yield self.trailer()
        return
    show.exposed = True
    """
        Starting streaming server
    """
    def start( self, folder, *args, **kw ):
        self.stream = StreamServerThread( self.log, self.__keyDirectory, folder, 4321 )
        if not self.stream:
            yield self.header( 'Test-Server' )
            yield """<h2>Status</h2><ul>
                        <li>Not running...</li></ul>"""
            yield self.trailer()
            return            
        # end if            
        raise cherrypy.HTTPRedirect('/status?folder=%s' % ( folder ) )
    # end def                              
    start.exposed = True
    """
        Stopping streaming server
    """   
    def stop( self, *args, **kw ):
        if self.stream:
            self.stream.join()
            self.stream = None
        else:
            yield self.header( 'Test-Server' )
            yield """<h2>Status</h2><ul>
                        <li>Not running...</li></ul>"""
            yield self.trailer()
            return                 
        # end if
        raise cherrypy.HTTPRedirect('/') 
    # end def                              
    stop.exposed = True
    """
        Status streaming server
    """   
    def status( self, folder, *args, **kw ):
        if self.stream:
            yield self.header( 'Test-Server', 10 )
            yield """<h2>Status</h2><ul>
                        <li>State : %s</li>
                        <li>Folder : %s</li>
                        <li>Event : %s</li>
                    </ul>
                    <div class='buttons'>
                        <li><a href='/stop?folder=%s'>STOP</a></li>
                    </div>
                    <ul>
                    """ % ( self.stream.State(), self.stream.folder, self.stream.event, self.stream.folder )
            for sess in self.stream.threads:
                yield "<li>%s</li>" % ( sess.port )
            # next 
            if len( self.stream.threads ) == 0:
                yield  "<li>No sessions</li>" 
            # end if                     
            yield "</ul>" + self.trailer()
        else:
            raise cherrypy.HTTPRedirect('/')
        # end if        
        return  
    # end def                              
    status.exposed = True

    """    
        /reg/registration
    """        
    def registration( self, *args, **kw ):
        return """<form action="/reg/register.asp" method="get">
                    <table>
                        <tr>
                            <td>UserName</td>
                            <td><input type='text' name="email"></td>                    
                        </tr>
                        <tr>
                            <td>Password</td>
                            <td><input type='password' name="password"></td>                    
                        </tr>
                        <tr>
                        </tr>
                        <tr>
                            <td></td>
                            <td></td>
                            <td><input type='submit' value='Subscribe'></td>
                        </tr>
                    </table>"""   
    # end def
    """    
        /reg/login
    """        
    def login( self, args, kw ):
        if users[ kw[ 'email' ] ] == kw[ 'password' ]:
            self.log.info( 'Building COOKIE' )
            cookie = cherrypy.response.cookie
            cookie[ 'USER' ] = "B83857BBF815665B944DE582A2D1CDBADEB0382DECFA32E2241B39B5096CFBACDD103815D6DB7295A5ED884FA691D063EAAE730740189312B1D22DB6F5BD357C9DB4F931B55C591ED0298693DE1A0816F92EC2EF299401CCCF12ED654FF79DD0BF8B0583055EE3A73EFEF10B31A2EA0016B7AEC56F9F41A50F497DD3CCE00764AFB1ED17A7C9E8771D655562A5EEB2DED18BA8670702BBEBD6B82FF5F896C358E916EFCF4CFB1EB4FDFC9DB38D03E37D51DFDF6CF2941EE13F6ADB620BF3D99584C00D67B98C45B169304A7EC4BB483F7B5B38B573A02C07528248C21302FBCF849D46B63AFC9EF633429D3AE404831D49D78737"
            cookie[ 'USER' ][ 'domain' ]      = '.pe2mbs.nl'
            cookie[ 'USER' ][ 'path' ] = '/'
            cookie[ 'USER' ][ 'max-age' ] = 3600
            cookie[ 'LOGIN' ] = '32E3C5BAF72A6DD0E80A01A0C6C29F5F00EA2DEF61A14A5FF09CBA47611087846545BCB3901CA57F4F6705DFC951F5B5A9B286E602911814AB3B6EB940EA6A2563265276C08B197496C54A07B87844439D71EA518A8EB9341DE78C824676BB173972EDD14099DD17BEAFB1C60B15D207112C305A74C85854F9DC7E5B9C4E3073E3BD595E0A8B42773A639B83D96DADDC53BB45975741E238FFCB03AE296BC477B7BAD70ED3C8D3D313B2A4609D79EE534E83E6EA80842F3846E0115E938B8F07331228E67CC1F21ABA1D75B9CD016EEF1B9E4A49AACF24D69F91CF0FBC922970CE2FD2F37750159985027D8927B036C710834ADD'
            cookie[ 'LOGIN' ][ 'domain' ]      = '.pe2mbs.nl'
            cookie[ 'LOGIN' ][ 'path' ] = '/'
            cookie[ 'LOGIN' ][ 'max-age' ] = 3600                                                   
            cookie[ 'LOGIN' ][ 'version' ]     = 1
            self.log.info( 'Redirect' )
            return True
        return False
    # end def                  

    """    
        /reg/getkey
    """        
    def getkey( self, filename, *args, **kw ):
        self.log.info( 'event : %s' % ( filename ) )
        folder = os.path.join( self.__keyDirectory, "E%06i" % ( int( filename ) ) )                
        keyfilename = os.path.join( folder, '%s.key' % ( filename ) )
        self.log.info( 'file : %s' % ( keyfilename ) )
        keyfile     = open( keyfilename, 'r' ) 
        key         = keyfile.read()
        self.log.info( 'From file %s => Key : [%s]' % ( keyfilename, key ) )
        keyfile.close()
        return key
    # end def
                      
    """    
        Service entry point for formula 1 streaming service
        
        http://hack:2080/reg/getkey/7341.asp?auth=B83857BBF815665B944DE582A2D1CDBADEB0382DECFA32E2241B39B5096CFBACDD103815D6DB7295A5ED884FA691D063EAAE730740189312B1D22DB6F5BD357C9DB4F931B55C591ED0298693DE1A0816F92EC2EF299401CCCF12ED654FF79DD0BF8B0583055EE3A73EFEF10B31A2EA0016B7AEC56F9F41A50F497DD3CCE00764AFB1ED17A7C9E8771D655562A5EEB2DED18BA8670702BBEBD6B82FF5F896C358E916EFCF4CFB1EB4FDFC9DB38D03E37D51DFDF6CF2941EE13F6ADB620BF3D99584C00D67B98C45B169304A7EC4BB483F7B5B38B573A02C07528248C21302FBCF849D46B63AFC9EF633429D3AE404831D49D78737
        http://hack:2080/reg/login?email=livef1@pe2mbs.nl&password=123456                

    """    
    def reg( self, *args, **kw ):
        REGISTER_URL		= "registration"        
        LOGIN_URL	    	= "login"
        KEY_URL_BASE		= "getkey"
        self.log.debug( repr( dict( args = args, kw = kw ) ) )
        if args[ 0 ] == LOGIN_URL:
            if self.login( args, kw ):
                return      
            # end if
            raise cherrypy.HTTPRedirect('/reg/message/loginnok.html')                    
        elif args[ 0 ] == REGISTER_URL:
            yield self.registration( args, kw )
        elif args[ 0 ] == KEY_URL_BASE:
            yield self.getkey( args[ 1 ].split( '.' )[ 0 ] )
        elif args[ 0 ] == 'register.asp':
            users[ kw[ 'email' ] ] = kw[ 'password' ]
            yield self.header( 'Test-Server' )
            yield 'You have created your user successfully.'
            yield "<table><thead><th>User</th><th>Password</th></thead><tbody>"
            
            for user in users:            
                yield "<tr><td>%s</td><td>%s</td></tr>" % ( user, users[ user ] )
            # next             
            yield "<tbody></table>" + self.trailer()
            yield self.trailer()                   
        else:
            if 'loginok.html' in args:
                yield 'You have been successfully logged in.'
            else:
                raise cherrypy.HTTPRedirect('/')
            # end if                                                                
        # end if                                                  
        return
    # end def
    reg.exposed = True

# end class

def StopReaderThread():
    if theApp.stream:
        theApp.stream.join()
    return
# end if    

def main():
    # cherrypy needs an absolute path to deal with static data
    theApp        = F1LiveServer()
    """
        This is to stop the reader thread
    """      
    StopReaderThread.priority = 10
    cherrypy.engine.subscribe( 'stop', StopReaderThread )
    cherrypy.quickstart( theApp, '/', config = os.path.join( os.path.join( os.getcwd(), 
                                            os.path.dirname( __file__ ) ), 'test-server.conf' ) )
    return

    