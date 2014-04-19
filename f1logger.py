#
#   livef1
#
#   f1logger.py - Logger module
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
import logging

def StartLogger():
  globalvar.log = logging.getLogger('live-f1')
  
  file_log_handler = logging.FileHandler('logfile.log')
  globalvar.log.addHandler( file_log_handler )

#  stderr_log_handler = logging.StreamHandler()
#  globalvar.log.addHandler( stderr_log_handler )

  # nice output format
  formatter = logging.Formatter( '%(asctime)s - %(filename)s %(funcName)s() [ %(lineno)d ] - %(levelname)s - %(message)s' )
  file_log_handler.setFormatter( formatter )
#   stderr_log_handler.setFormatter( formatter )
  globalvar.log.setLevel(10)



