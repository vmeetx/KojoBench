cleari()

def shape = Picture {
    val circles_radi = Array(100, 70, 40)
    
    
    setHeading(0)
    
    left(360, circles_radi(2))
    left(360, circles_radi(1))
    left(360, circles_radi(0))
}

drawCentered(shape)
