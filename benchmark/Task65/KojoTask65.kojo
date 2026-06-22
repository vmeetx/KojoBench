cleari()

def shape = Picture {
    val semicircle_radius = 100
    
    
    setHeading(0)
    
    left(90)
    repeat(3) {
      left(180, semicircle_radius)
      left(60)
    }
}

drawCentered(shape)
