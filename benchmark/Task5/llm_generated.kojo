cleari()

def shape = Picture {
    // Draw the large triangle
    forward(200)
    right(120)
    forward(200)
    right(120)
    forward(200)
    right(120)
    
    // Save position and heading for the small triangles
    savePosHe()
    
    // Move to the left corner of the large triangle
    left(60)
    forward(100)
    right(90)
    forward(50)
    left(90)
    forward(100)
    
    // Draw the small triangle on the left corner
    repeat(3) {
      forward(100)
      right(120)
    }
    
    // Restore position and heading
    restorePosHe()
    
    // Move to the right corner of the large triangle
    right(60)
    forward(100)
    left(90)
    forward(50)
    right(90)
    forward(100)
    
    // Draw the small triangle on the right corner
    repeat(3) {
      forward(100)
      left(120)
    }
    
    // Restore position and heading
    restorePosHe()
    
    // Move to the top corner of the large triangle
    left(60)
    forward(100)
    right(90)
    forward(50)
    left(90)
    forward(100)
    
    // Draw the small triangle on the top corner
    repeat(3) {
      forward(100)
      right(120)
    }
}

drawCentered(shape)
