cleari()

def shape = Picture {
    val circle_radius = 100
    
    
    setHeading(0)
    
    forward(circle_radius * 2)
    left(540, circle_radius)
    forward(circle_radius * 2)
    left(540, circle_radius)
}

drawCentered(shape)
