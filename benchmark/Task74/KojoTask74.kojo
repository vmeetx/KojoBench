cleari()

def shape = Picture {
    val square_side = 200
    
    
    setHeading(0)
    
    setHeading(90)
    repeat(3) {
      forward(square_side)
      right(90)
    }
}

drawCentered(shape)
