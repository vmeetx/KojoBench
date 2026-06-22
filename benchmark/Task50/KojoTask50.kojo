cleari()

def shape = Picture {
    val small_circle_radius = 100
    
    
    setHeading(0)
    
    repeat(4) {
            left(360, small_circle_radius)
            right(90)
    }
    left(180, small_circle_radius)
}

drawCentered(shape)
