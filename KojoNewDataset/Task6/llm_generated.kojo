clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
val triangle_side = 200


def drawPolygon(sides: Int, length: Double) {
  val turn = 360.0 / sides
  repeat(sides) {
    forward(length)
    right(turn)
  }
}

drawPolygon(3, triangle_side)
left(120)
drawPolygon(3, triangle_side)