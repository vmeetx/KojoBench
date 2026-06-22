cleari()

def shape = Picture {
    val largest_square_side = 200
    
    
    setHeading(0)
    
    repeat(4) {
      forward(largest_square_side)
      right(90)
    }
    forward(largest_square_side / 2)
    right(45)
    repeat(4) {
      forward(largest_square_side * math.sqrt(2) / 2)
      right(90)
    }
}

drawCentered(shape)
