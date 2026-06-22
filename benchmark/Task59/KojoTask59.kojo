cleari()

def shape = Picture {
    val largest_square_side = 200
    val smallest_square_side = 50
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    repeat(4) {
      draw_polygon(4, largest_square_side / 2)
      right(90)
    }
    forward(smallest_square_side)
    right(90)
    forward(smallest_square_side)
    right(90)
    draw_polygon(4, largest_square_side / 2)
}

drawCentered(shape)
