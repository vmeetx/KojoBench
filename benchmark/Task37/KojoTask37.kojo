cleari()

def shape = Picture {
    val half_lines_length = 50
    val semicircle_radius = 50
    
    
    setHeading(0)
    
    forward(half_lines_length)
    right(90)
    right(180, semicircle_radius)
    right(90)
    forward(half_lines_length)
}

drawCentered(shape)
