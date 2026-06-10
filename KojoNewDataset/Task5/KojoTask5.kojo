clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
val small_triangle_side = 50
val large_triangle_side = 100

def draw_polygon(sides: Int, length: Double) {
  left(60)
  var outer_turn = 360 / sides
  repeat(sides.toInt) {
    forward(length)
    right(outer_turn)
  }
  right(60)
}
right(60)
repeat(3) {
  draw_polygon(3, small_triangle_side)
  right(120)
  forward(large_triangle_side)
}
