cleari()

def shape = Picture {
    val radius = 100
    
    
    setHeading(0)
    
    left(360, radius)
    left(90, radius)
    left(90)
    forward(2 * radius)
    left(90)
    left(90, radius)
    left(90)
    forward(2 * radius)
}

drawCentered(shape)
