import array
import copy

class ByteBuffer( object ):
    def __init__( self, value = None ):
        self.clear()
        if type( value ) == type( self ):
            self.__data   = copy.copy( value )
        else: 
            if value:
                self.set( value )
            # end if
        # end if
        return
    # end def
    
    def reset( self ):
        self.__index = 0        
        return
    # end def
    
    def clear( self ):
        self.__data   = array.array( 'B' )
        self.__index  = 0
        return  
    # end def

    def size( self ):
        return len( self.__data ) - self.__index - 1        
    # end def
    
    def __len__( self ):
        return len( self.__data )
    # end def
           
    length = property( __len__ )

    def getIndex( self ):
        return self.__index
    # end def
    
    index  = property( getIndex )
    
    def set( self, value ):
        self.__index = 0
        if type( value ) == type( array.array('B') ):
            self.__data   = copy.copy( value ) 
        elif type( value ) == int:
            self.__data.append( value )
        elif type( value ) == str:
            self.__data   = array.array( 'B', value )                     
        # end if        
        return                    
    # end def
    
    def append( self, value ):
        if type( value ) == type( array.array('B') ):
            for c in value:
                self.__data += c
            # next
        elif type( value ) == str:
            for c in value:
                self.__data.append( ord( c ) )
            # next 
        elif type( value ) == int:
            self.__data.append( value )
        return                                        
    # end def              
    
    def next( self ):
        if self.__index < len( self.__data ):
            self.__index += 1
            return self.__data[ self.__index - 1 ]
        # end if
        raise StopIteration
    # end def              
        
    def __iter__( self ):
        return self
    # end def
        
    def __toString( self ):
        return ''.join( '{:s}'.format( chr( x ) ) for x in self.__data )
    # end def

    def __fromString( self, value ):
        self.__data   = array.array( 'B', value )
        self.__index = 0       
        return
    # end def

    String = property( __toString, __fromString ) 

    def __toBytes( self ):
        return copy.copy( self.__data )
    # end def

    def __fromBytes( self, value ):
        self.__data   = copy.copy( value )
        self.__index = 0       
        return
    # end def

    Bytes = property( __toBytes, __fromBytes ) 

    def __toHexString( self ):
        return ''.join( '{:02X}'.format( x ) for x in self.__data )
    # end def

    def __fromHexString( self, value ):
        self.__data = array.array('B', value.decode( 'hex' ) )
        self.__index = 0                        
        return
    # end def
    
    Hex = property( __toHexString, __fromHexString )

    def copy( self ):
        return copy.copy( self.__data ) 
    # end def
                
    def __getitem__( self, idx ):
        return self.__data[ idx ]            
    # end def

    def __setitem__( self, idx, value ):
        self.__data[ idx ] = value
        return
    # end def
    
    def __getslice__( self, i, j ):
        return ByteBuffer( self.__data[ i : j ] ) 
    # end def

    def __setslice__( self, i, j, sequence ):
        if type( sequence ) == type( self ): 
            self.__data[ i : j ] = sequence.copy()
        else:
            self.__data[ i : j ] = sequence
        return
    # end def
    
    def __delslice__( self, i, j ):
        del  self.__data[ i : j ]
        return
    # end def
                
    def __iadd__( self, other ):    # +=
        if type( other ) == int:
            self.__data.append( other )
        elif type( other ) == str:
            self.__data += array.array( 'B', other )
        elif type( other ) == type( array.array('B') ):
            self.__data += other
        return
    # end def
    
    def __add__( self, other ):     # +
        result = ByteBuffer()                  
        result += other 
        return result 
    # end def

    def __radd__( self, other ):    # +
        result = ByteBuffer()                  
        result += other 
        return result 
    # end def

    def __lt__( self, other ):  # <
        if type( value ) == type( self ):
            return value.copy() < self.__data
        return False 
    # end def
    
    def __le__( self, other ):  # <=
        if type( value ) == type( self ):
            return value.copy() <= self.__data
        return False 
    # end def
        
    def __eq__( self, other ):  # ==
        if type( value ) == type( self ):
            return value.copy() == self.__data
        return False 
    # end def
        
    def __ne__( self, other ):  # not ==
        if type( value ) == type( self ):
            return not value.copy() == self.__data
        return False 
    # end def
    
    def __gt__( self, other ):  # > 
        if type( value ) == type( self ):
            return value.copy() > self.__data
        return False 
    # end def
    
    def __ge__( self, other ):  # >=
        if type( value ) == type( self ):
            return value.copy() >= self.__data
        return False 
    # end def     
    
    def read( self, length ):
        if length:        
            if type( length ) == int:
                result = ''.join( '{:s}'.format( chr( x ) ) for x in self.__data[ self.__index : self.__index + length ] )
                self.__index += length
                return result
            # end if
        else:
            self.__index = len( self.__data )         
            return self.String
        return None
    # end def     

    def write( self, value ):
        self.__iadd__( value ) 
        return             
    # end def     
    """
        This returns a byte
    """        
    def readByte( self ):
        result = self.__data[ self.__index ]
        self.__index += 1 
        return result
    # end def     
    """
        This returns a string
    """        
    def readString( self, length ):
        result = ''.join( '{:s}'.format( chr( x ) ) for x in self.__data[ self.__index : self.__index + length ] )
        self.__index += length
        return result    
    # end if                                                     
    """
        This returns an array of bytes
    """        
    def readBytes( self, length ):
        result =  self.__data[ self.__index : self.__index + length ]
        self.__index += length
        return result
    # end if      
    
    
    def isprint( self ):
        for x in self.__data:
            if x < 0x20 or x > 0x7F:
                return False
            # end if
        # next                      
        return True      
                                                   
# end class

def __tests():
    print( "Test" )
    myList = []
            
    myList.append( ByteBuffer( "HELLO WORLD" ) )
    
    myList.append( ByteBuffer( range( 0x30, 0x3A ) ) )
    
    myList.append( ByteBuffer( 0x41 ) )
    myList[ 2 ].append( 0x42 )
    myList[ 2 ].append( 0x43 )
    myList[ 2 ].append( 0x44 )
    myList[ 2 ].append( 0x45 )
    myList[ 2 ].append( 0x46 )
    myList[ 2 ].append( 0x47 )
    myList[ 2 ].append( 0x48 )
    myList[ 2 ].append( 0x49 )

    myList.append( ByteBuffer() )
    myList[ 3 ].String = "This is a test"

    myList.append( ByteBuffer() )
    myList[ 4 ].Hex = myList[ 0 ].Hex
    
    for buff in myList:     
        print( "string : %s" % ( buff.String ) )
        print( "hex    : %s" % ( buff.Hex ) )
        print( ''.join( '{:s}, '.format( chr( x ) ) for x in buff ) )        

        buff.reset()
        buff.append( 10 )
        buff.append( "MARC" )
        print( ''.join( '{:02X}'.format( x ) for x in buff ) )

        print( "string : %s" % ( buff.String ) )      
        print( "length  = %i" % ( buff.length ) )
        print( "index   = %i" % ( buff.index ) )     
        print( "slice   = %s" % ( buff[ 6 : 11 ]  ) )
        print( "4       = %i" % ( buff[ 4 ] ) )
        print( "6       = %i" % ( buff[ 6 ] ) )     
    # end if       
    print( "Done" )
    return
    
if __name__ == "__main__":
    __tests()

