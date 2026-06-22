cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val triangle_side = 200
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    setHeading(60)
    repeat(2) {
      draw_polygon(3, triangle_side)
      left(120)
    }
}

drawCentered(shape)
