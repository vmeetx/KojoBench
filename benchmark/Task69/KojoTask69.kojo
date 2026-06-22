cleari()

def shape = Picture {
    val semicircle_radius = 100
    
    
    setHeading(0)
    
    repeat(4) {
      forward(2 * semicircle_radius)
      left(90)
      right(180, semicircle_radius)
      left(90)
      forward(2 * semicircle_radius)
      right(90)
    }
}

drawCentered(shape)
