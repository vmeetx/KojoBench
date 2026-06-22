cleari()

def shape = Picture {
    val square_side = 200
    val semicircle_radius = 40
    
    
    setHeading(0)
    
    repeat(4) {
      forward((square_side-semicircle_radius)/2)
      right(90)
      right(180, semicircle_radius)
      right(90)
      forward((square_side-semicircle_radius)/2)
      left(90)
    }
}

drawCentered(shape)
