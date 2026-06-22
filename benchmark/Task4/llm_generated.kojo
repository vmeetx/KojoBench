cleari()

def shape = Picture {
    // Draw the bottom straight line
    forward(200)
    
    // Turn right and draw the first side going up and outward
    right(72)
    forward(150)
    
    // Turn left and draw the second side going up and outward
    left(144)
    forward(150)
    
    // Turn right and draw the third side coming together to meet at a single point at the top
    right(72)
    forward(150)
    
    // Turn left and draw the fourth side coming together to meet at a single point at the top
    left(144)
    forward(150)
}

drawCentered(shape)
