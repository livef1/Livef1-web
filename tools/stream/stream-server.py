import socket, threading
import logging

class StreamClientThread(threading.Thread):
    def __init__( self, clientsock, ip, port, log, folder, event ):
        threading.Thread.__init__( self )
        self.running    = False 
        self.ip         = ip
        self.port       = port
        self.clientsock = clientsock
        self.folder     = folder
        self.log        = log
        self.sequence   = 0
        self.event      = event
        self.log        = logging.getlogger( "test-server" )
        self.log.debug( "[+] New thread started for %s:%i" % ( ip, port ) )
        return
    # end def

    def run( self ):
        self.running    = True 
        self.log.debug( "Connection from %s:%i" % ( ip, port ) )    
        self.clientsock.send( "Welcome to the server\n\n" )
        data = "dummydata"

        while self.running and len( data ):
            data = self.clientsock.recv( 1 )           
            self.log.debug( "Client sent : %s" % ( data )
        # end while
        self.log.debug( "Client disconnected %s:%i" % ( ip, port ) )    
        return
    # end def
# end class        

class StreamServerThread( threading.Thread ):
    def __init__( self, log, folder, event, port ):
        self.port       = port
        self.host       = '0.0.0.0'
        self.backlog    = 1
        self.running    = 0
        self.log        = log
        self.tcpsock    = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.tcpsock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.tcpsock.bind( ( self.host, self.port ) )
        self.threads    = []
        self.folder     = folder
        self.event      = event
        return
    # end def 

    def run( self ):
        self.log.debug(  "run" )
        self.running    = True 
        while self.running:
            tcpsock.listen( self.backlog )
            self.log.debug(  "Listening for incoming connections..." )
            (clientsock, ( ip, port ) ) = tcpsock.accept()
            newthread = StreamClientThread( clientsock, ip, port, self.log, self.folder, self.event )
            newthread.start()
            threads.append( newthread )
        # end while   
        tcpsock.close()
        self.log.debug(  "server shutting down" )                 
        for t in threads:
            t.join()
        # next                    
        self.log.debug(  "run" )
        return
    # end def 

    def stopit( self ):
        self.running = False
        for t in threads:
            t.join()
        return;
    # end def 
# end class
     