cleari()

def shape = Picture {
    // Draw the square
    forward(200)
    right(90)
    forward(200)
    right(90)
    forward(200)
    right(90)
    forward(200)
    right(90)
    
    // Move to the center of the square and draw the circle
    penUp()
    forward(100)
    left(90)
    forward(100)
    penDown()
    
    setPenColor(blue)
    circle(100)
}

drawCentered(shape)
