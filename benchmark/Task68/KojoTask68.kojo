cleari()

def shape = Picture {
    val semicircle_radius = 50
    
    
    setHeading(0)
    
    repeat(4) {
      left(180, semicircle_radius)
      right(90)
    }
    left(90)
    repeat(4) {
      forward(2 * semicircle_radius)
      left(90)
    }
}

drawCentered(shape)
