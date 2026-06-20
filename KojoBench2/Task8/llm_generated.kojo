cleari()

def shape = Picture {
    // Draw a square in the center
    repeat(4) {
      forward(100)
      right(90)
    }
    
    // Add triangles on each side of the square
    repeat(4) {
      // Move diagonally up-left from current position
      forward(50)
      left(45)
      
      // Draw triangle pointing outward
      forward(35.355) // Approximately sqrt(2500 + 1250*sqrt(2))
      right(90)
      forward(35.355)
      left(45)
    }
    
    // Connect the outer vertices to form the star
    forward(70.71) // Approximately distance between two opposite triangles
    right(45)
    
    forward(70.71)
    left(45)
    
    forward(70.71)
    left(45)
    
    forward(70.71)
    right(45)
}

drawCentered(shape)
