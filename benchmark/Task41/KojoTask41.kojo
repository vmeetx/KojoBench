cleari()

def shape = Picture {
    val triangle_side = 200
    val semicircle_radius = 40
    
    
    setHeading(0)
    
    repeat(3) {
      forward((triangle_side-semicircle_radius)/2)
      right(90)
      right(180, semicircle_radius)
      right(90)
      forward((triangle_side-semicircle_radius)/2)
      left(120)
    }
}

drawCentered(shape)
