cleari()

def shape = Picture {
    val large_semicircle_radius = 120
    
    
    setHeading(0)
    
    right(90)
    right(180, large_semicircle_radius)
    left(180, large_semicircle_radius/2)
    right(180)
    left(180, large_semicircle_radius/2)
}

drawCentered(shape)
