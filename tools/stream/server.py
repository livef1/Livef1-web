import os
import time
import array
import socket, threading
import logging
from src.packet     import F1Packet   
from src.stream     import F1Stream

class STATE( object ):
    RUNNING = 2
    STOPPING = 1
    STOPPED = 0     


class StreamClientThread(threading.Thread):
    def __init__( self, clientsock, ip, port, log, folder, event ):
        threading.Thread.__init__( self )
        self.state      = STATE.STOPPED 
        self.ip         = ip
        self.port       = port
        self.clientsock = clientsock
        self.folder     = folder
        self.log        = log
        self.sequence   = 0
        self.event      = event
        self.stream     = F1Stream( log )
        self.packet     = F1Packet( log )
        self.log.debug( "[+] New client reader thread started for %s:%i" % ( ip, port ) )
        self.start()       
        return
    # end def

    def run( self ):
        self.running    = STATE.RUNNING 
        self.log.debug( "Connection from %s:%i" % ( self.ip, self.port ) )    
        basedir = os.path.join( self.folder, self.event )
        filename = os.path.join( basedir, 'keyframe_seq_%05i.bin' % ( self.sequence ) )
        self.log.debug( "looking for file : %s" % ( filename ) )
        if os.path.isfile( filename ):
            filestream = open( filename, 'r' )
            if not filestream:
                self.log.debug( "file NOT open: %s" % ( filename ) )
            else:                                
                self.log.debug( "reading from file : %s at pos %i" % ( filename, filestream.tell() ) )
                block = array.array( 'B', filestream.read() )
                self.log.debug( "read from file : %s at pos %i" % ( filename, filestream.tell() ) )
                self.log.debug( "DATA : [%s]" % ( ''.join('{:02X}'.format(x) for x in block ) ) )                          
                filestream.close()
                self.stream.Set( block )
                self.log.debug( "Block set" )
                self.sequence += 1
                while self.running == STATE.RUNNING:
                    data = self.clientsock.recv( 1 )
                    if len( data ) == 0:
                        break
                    # endif 
                    data = array.array( 'B', data )
                    # self.log.debug( "RECV: [%s]" % ( ''.join('{:02X}'.format(x) for x in data ) ) )
                    for d in data:                    
                        if d == 0x10:
                            do_eof = False
                            # request next block
                            if self.packet.set( self.stream ):
                                block = self.packet.rawData()
                                if len( block ) == 0:
                                    # end if file reached
                                    do_eof = True
                                else:    
                                    self.log.debug( "SEND: [%s]" % ( ''.join('{:02X}'.format(x) for x in block ) ) ) 
                                    self.clientsock.send( block )
                                    data = []
                                # end if                  
                            else:
                                do_eof = True
                            # end if
                            if do_eof:                                                             
                                # load a new file
                                filename = os.path.join( basedir, 'keyframe_seq_%05i.bin' % ( self.sequence ) ) 
                                if os.path.exists( filename ):
                                    self.sequence += 1
                                    filestream = open( filename, 'r' )
                                    self.stream.Reset()
                                    block = array.array( 'B', filestream.read() )
                                    self.stream.Set( block )            
                                    filestream.close()
                                # end if                        
                            # end if                        
                            # self.clientsock.send( "Welcome to the server\n\n" )
                        # endif
                    # next                                           
                # end while
                self.clientsock.shutdown( socket.SHUT_RDWR )
                self.clientsock.close()
                self.log.debug( "Client disconnected %s:%i" % ( self.ip, self.port ) )
            # end if        
        else:
            self.log.debug( "file NOT found : %s" % ( filename ) )
        # end if        
        self.running    = STATE.STOPPED   
        return
    # end def
    
    def join( self ):
        if self.state == STATE.RUNNING:
            self.log.debug(  "stopping client reader" )
            self.state = STATE.STOPPING
            self.tcpsock.shutdown( socket.SHUT_RDWR )
            self.tcpsock.close()
            time.sleep( 0.1 )
            if not self.state == STATE.STOPPED:
                threading.Thread.join( self )
            # end if
        else:
            self.log.debug(  "client not running" )            
        # end if            
        self.state = STATE.STOPPED
        return
    # end def
        
# end class        

class StreamServerThread( threading.Thread ):
    def __init__( self, log, folder, event, port ):
        threading.Thread.__init__( self )
        self.port       = port
        self.host       = '0.0.0.0'
        self.backlog    = 1
        self.state      = STATE.STOPPED
        self.log        = log
        self.tcpsock    = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.tcpsock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.tcpsock.bind( ( self.host, self.port ) )
        self.threads    = []
        self.folder     = folder
        self.event      = event
        self.start()
        return
    # end def 

    def State( self ):
        if self.state == STATE.STOPPED:
            return "Stopped"
        elif self.state == STATE.RUNNING:
            return "Running"
        elif self.state == STATE.STOPPING:
            return "Stopping"
        return ""            
    # end def

    def run( self ):
        self.log.debug(  "run enter" )
        self.state    = STATE.RUNNING 
        while self.state == STATE.RUNNING:
            self.tcpsock.listen( self.backlog )
            self.log.debug(  "Listening for incoming connections..." )
            try:
                (clientsock, ( ip, port ) ) = self.tcpsock.accept()
            except:
                self.log.debug(  "Got break..." )
                break            
            else:
                self.log.debug(  "Got accept..." )            
                newthread = StreamClientThread( clientsock, ip, port, self.log, self.folder, self.event )
                self.threads.append( newthread )
            # end try
            for thr in self.threads:
                if thr.state == STATE.STOPPED:
                    self.threads.remove( thr )
                # end if
            # next                                                                                            
        # end while
        try:
            self.tcpsock.shutdown( socket.SHUT_RDWR )
            self.tcpsock.close()
        except:
            self.log.debug(  "exception" )    
        self.log.debug(  "server shuting down" )                 
        for t in self.threads:
            self.log.debug(  "a thread" )
            t.join()
        # next
        self.state = STATE.STOPPED
        self.log.debug(  "run leave" )
        return
    # end def 

    def join( self ):
        if self.state == STATE.RUNNING: 
            self.log.debug(  "stopping server" )
            self.state = STATE.STOPPING
            self.tcpsock.shutdown( socket.SHUT_RDWR )
            self.tcpsock.close()
            time.sleep( 0.1 )            
            if not self.state == STATE.STOPPED:
                threading.Thread.join( self )
                #for t in self.threads:
                #    t.join()
                # next
            # end if  
        else:
            self.log.debug(  "server not running" )        
        # end if            
        self.state = STATE.STOPPED
        return;
    # end def 
# end class
