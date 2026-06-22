cleari()

def shape = Picture {
    val side = 80
    
    
    setHeading(0)
    
    repeat(4) {
      forward(side)
      left(90)
      forward(side)
      right(90)
      forward(side)
      right(90)
    }
}

drawCentered(shape)
