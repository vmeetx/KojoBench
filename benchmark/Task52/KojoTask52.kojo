cleari()

def shape = Picture {
    val square_side = 200
    
    
    setHeading(0)
    
    repeat(8) {
      forward((1 + math.sqrt(2)) * square_side / (2 + math.sqrt(2)))
      right(45)
      forward((1 + math.sqrt(2)) * square_side / (2 + math.sqrt(2)))
      right(90)
    }
}

drawCentered(shape)
