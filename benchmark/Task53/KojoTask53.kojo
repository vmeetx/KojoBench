cleari()

def shape = Picture {
    val radius = 100
    
    
    setHeading(0)
    
    left(270, radius)
    left(90)
    forward(radius)
    right(90)
    forward(radius)
}

drawCentered(shape)
