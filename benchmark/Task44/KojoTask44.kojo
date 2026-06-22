cleari()

def shape = Picture {
    val semicircle_radius = 20
    
    
    setHeading(0)
    
    repeat(3) {
      right(180, semicircle_radius)
      right(180)
      left(180, semicircle_radius)
      right(180)
    }
}

drawCentered(shape)
