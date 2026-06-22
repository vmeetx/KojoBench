cleari()

def shape = Picture {
    val line_segment = 80
    val square_side = 40
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    repeat(3) {
      forward(line_segment)
      draw_polygon(4, square_side)
      forward(-line_segment)
      right(120)
    }
}

drawCentered(shape)
