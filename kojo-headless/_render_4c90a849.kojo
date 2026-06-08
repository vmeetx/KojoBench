clear()
setSpeed(fast)
val small_hexagon_side = 100
setHeading(0)
def draw_polygon(sides: Int, length: Double) {
  var outer_turn = 360 / sides
  repeat(sides.toInt) {
    forward(length)
    right(outer_turn)
  }
}
repeat(6) {
  draw_polygon(6, small_hexagon_side)
  right(60)
}