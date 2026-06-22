cleari()

def shape = Picture {
    // Draw the left triangle
    forward(100)
    right(120)
    forward(100)
    right(120)
    forward(100)
    right(120)
    
    // Move to the shared corner and draw the right triangle
    penUp()
    forward(50)
    left(90)
    forward(50)
    penDown()
    
    forward(100)
    right(120)
    forward(100)
    right(120)
    forward(100)
    right(120)
}

drawCentered(shape)
