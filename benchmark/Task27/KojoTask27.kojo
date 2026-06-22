cleari()

def shape = Picture {
    val square_side = 200
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    draw_polygon(4, square_side)
    left(-135)
    right(360, square_side/2 * math.sqrt(2))
}

drawCentered(shape)
