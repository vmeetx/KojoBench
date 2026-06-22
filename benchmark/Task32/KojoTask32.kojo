cleari()

def shape = Picture {
    val radius = 100
    
    
    setHeading(0)
    
    left(360, radius)
    right(180)
    left(360, radius)
    right(90)
    forward(2 * radius)
}

drawCentered(shape)
