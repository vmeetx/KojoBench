cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val square_side = 200
    
    repeat(4) {
      forward(square_side)
      right(90)
    }
}

drawCentered(shape)
