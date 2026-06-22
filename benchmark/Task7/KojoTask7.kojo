cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val triangle_side = 100
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    setHeading(-30)
    draw_polygon(3, triangle_side)
    right(60)
    draw_polygon(4, triangle_side)
}

drawCentered(shape)
