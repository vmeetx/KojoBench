clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
val large_triangle_side = 100
val small_triangle_side = 50

def drawPolygon(sides: Int, length: Double) {
  val turn = 360.0 / sides
  repeat(sides) {
    forward(length)
    right(turn)
  }
}


right(60)
repeat(3) {
  left(60)
  drawPolygon(3, small_triangle_side)
  right(60)
  forward(large_triangle_side)
}