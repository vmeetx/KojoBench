cleari()

def shape = Picture {
    val square_side = 100
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    setHeading(0)
    draw_polygon(4, square_side)
    right(180)
    draw_polygon(4, square_side)
}

drawCentered(shape)
