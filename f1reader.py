#
#   livef1
#
#   f1reader.py - reader task running under the web-server
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
import time
import f1logger
import f1stream
import logging
log  = logging.getLogger('live-f1')

def CheckIt():
    #
    #   This is just a dummy to keep the loop processing
    #
    #log.info( 'Waiting ...' )
    return

def ReaderSession( Sess ):
    run     = 1
    tries   = 0
    while run:
        Sess.parse( Sess.obtain_key_frame() )
        if ( Sess.open() ):
            while ( Sess.read() > 0 ):
                CheckIt()
                continue
            # end while
            #
            #   Posible to get here from a decryption error, so just recycle the session 
            Sess.close()
            tries = 0
        else:   
            # stop the thread for now
            log.error( "Error %s ...." % Sess.error )
            if tries > 5:
                log.error( "Error connecting, try %i of 5" % ctries )
                run = 0
            else:
                tries += 1
            # end if     
        # end if  
    # end while
    return

def Reader( theApp ):
    log.info( 'Live F1 reader thread starting ...' )
    run         = 1
    tries       = 0
    while run:
        crun        = 0
        username    = theApp.config.get( 'registration', 'user' )
        passwd      = theApp.config.get( 'registration', 'passwd' )
        log.debug( "user = %s, passwd = %s" % ( username, passwd ) )
        Sess = f1stream.f1session( globalvar.theApp, username, passwd )            
        key_val = Sess.obtain_auth_cookie()
        if not key_val:
            log.warning( "Error getting cookie, try %i of 5" % tries )
            tries   += 1
        else:
            log.info( "Got authentication cookie: %s" % ( key_val ) )
            crun    = 1
            ctries  = 0
        # end if   
        if key_val:               
            ReaderSession( Sess )
        if tries > 5:
            log.error( "Error getting cookie, try %i of 5" % tries )
            run = 0
        #end if
    # end while
    log.error( "Exiting the THREAD" )
    exit()    
    return
    
