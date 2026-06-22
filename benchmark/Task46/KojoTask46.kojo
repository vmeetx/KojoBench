cleari()

def shape = Picture {
    val line_segment = 80
    val circle_radius = 20
    
    
    setHeading(0)
    
    repeat(3) {
      forward(line_segment)
      left(360, circle_radius)
      forward(-line_segment)
      right(120)
    }
}

drawCentered(shape)
