cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val pentagon_side = 200
    
    setHeading(36)
    repeat(5) {
      forward(pentagon_side)
      right(72)
    }
}

drawCentered(shape)
