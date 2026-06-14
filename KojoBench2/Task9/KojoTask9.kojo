cleari()

def shape = Picture {
    setHeading(180)
    setPenColor(black)
    val semicircle_radius = 70
    
    right(180, semicircle_radius)
    left(180, semicircle_radius)
    left(90)
    forward(4 * semicircle_radius)
}

drawCentered(shape)
