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

username		= "mbertens@xs4all.nl"
password		= "5701mb"

def CheckIt():
    #
    #   This is just a dummy to keep the loop processing
    #
    #globalvar.log.info( 'Waiting ...' )
    return

def Reader( name, index ):
    globalvar.theApp.info( '%s thread starting ...' % ( name ) )
    run = 1
    tries = 0
    while run:
        Sess = f1stream.f1session( globalvar.theApp, username, password )            
        key_val = Sess.obtain_auth_cookie()
        if not key_val:
            globalvar.theApp.warning( "Error getting cookie, try %i of 5" % tries )
            tries = tries + 1
        else:
            globalvar.theApp.info( "Got authentication cookie: %s" % ( key_val ) )
            run = 1
            ctries = 0
        # end if            
        while run and key_val:
            Sess.parse( Sess.obtain_key_frame() )
            if ( Sess.open() ):
                while ( Sess.read() > 0 ):
                    CheckIt()
                # end while
                #
                #   Posible to get here from a decryption error, so just recycle the session 
                Sess.close()
                tries = 0
                ctries = 0
                run = 1  
            else:   
                # stop the thread for now
                globalvar.theApp.error( "Error %s ...." % Sess.error )
                if ctries > 5:
                    globalvar.theApp.error( "Error connecting, try %i of 5" % ctries )
                    run = 0
                else:
                    ctries += 1    
            # endif  
        # end while
        if tries > 5:
            globalvar.theApp.error( "Error getting cookie, try %i of 5" % tries )
            run = 0
        #endif
    # end while
    globalvar.theApp.error( "Exiting the THREAD" )
    exit()    
    return
    
