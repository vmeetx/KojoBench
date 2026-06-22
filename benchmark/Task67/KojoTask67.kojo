cleari()

def shape = Picture {
    val semicircle_radius = 100
    
    
    setHeading(0)
    
    repeat(4) {
      left(180, semicircle_radius)
      left(90)
      forward(2 * semicircle_radius)
    }
}

drawCentered(shape)
