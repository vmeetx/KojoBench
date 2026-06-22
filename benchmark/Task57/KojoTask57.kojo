cleari()

def shape = Picture {
    val large_triangle_side = 150
    val small_triangle_side = 75
    
    
    setHeading(0)
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    left(60)
    draw_polygon(3, large_triangle_side)
    right(60)
    forward(small_triangle_side)
    left(60)
    draw_polygon(3, large_triangle_side)
}

drawCentered(shape)
