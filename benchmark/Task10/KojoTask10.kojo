cleari()

def shape = Picture {
    setHeading(0)
    setPenColor(black)
    val circle_radius = 100
    
    def draw_polygon(sides: Int, length: Double) {
      var outer_turn = 360 / sides
      repeat(sides.toInt) {
        forward(length)
        right(outer_turn)
      }
    }
    left(360, circle_radius)
    left(180)
    forward(circle_radius)
    right(90)
    draw_polygon(4, 2 * circle_radius)
}

drawCentered(shape)
