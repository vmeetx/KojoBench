cleari()

def shape = Picture {
    // Draw the tilted square
    right(45)
    forward(200)
    right(90)
    forward(200)
    right(90)
    forward(200)
    right(90)
    forward(200)
    left(45)
    
    // Draw the four triangles
    def drawTriangle() {
      forward(100)
      right(135)
      forward(141.4) // Hypotenuse of a 45-45-90 triangle with leg length 100
      right(135)
      forward(100)
    }
    
    // Upper-left triangle
    left(45)
    drawTriangle()
    
    // Upper-right triangle
    right(90)
    drawTriangle()
    
    // Lower-left triangle
    right(90)
    drawTriangle()
    
    // Lower-right triangle
    right(90)
    drawTriangle()
}

drawCentered(shape)
