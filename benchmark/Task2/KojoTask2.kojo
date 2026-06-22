cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val triangle_side = 200
    
    setHeading(60)
    repeat(3) {
      forward(triangle_side)
      right(120)
    }
}

drawCentered(shape)
