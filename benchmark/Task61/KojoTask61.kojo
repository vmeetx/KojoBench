cleari()

def shape = Picture {
    val semicircle_radius = 100
    
    
    setHeading(0)
    
    left(90)
    left(180, semicircle_radius)
    left(90)
    forward(2 * semicircle_radius)
}

drawCentered(shape)
