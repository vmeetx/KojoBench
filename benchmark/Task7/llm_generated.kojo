cleari()

def shape = Picture {
    // Draw the square
    forward(100)
    right(90)
    forward(100)
    right(90)
    forward(100)
    right(90)
    forward(100)
    right(90)
    
    // Move to the starting point of the triangle
    penUp()
    forward(50)
    left(90)
    forward(50)
    penDown()
    
    // Draw the triangle
    forward(100)
    right(120)
    forward(100)
}

drawCentered(shape)
