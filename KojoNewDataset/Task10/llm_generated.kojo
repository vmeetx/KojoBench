clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
val circle_radius = 100


left(360, circle_radius)

def drawPolygon(sides: Int, length: Double) {
  val turn = 360.0 / sides
  repeat(sides) {
    forward(length)
    right(turn)
  }
}

drawPolygon(4, 2 * circle_radius)