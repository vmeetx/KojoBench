cleari()

def shape = Picture {
    val large_circle_radius = 100
    val small_circle_radius = 50
    
    
    setHeading(0)
    
    setHeading(90)
    left(360, large_circle_radius)
    right(180)
    left(360, small_circle_radius)
}

drawCentered(shape)
