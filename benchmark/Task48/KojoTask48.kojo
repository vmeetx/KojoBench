cleari()

def shape = Picture {
    val squares_sides = Array(40, 80, 120, 160)
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    repeatFor(0 until 4) { i =>
      draw_polygon(4, squares_sides(i))
    }
}

drawCentered(shape)
