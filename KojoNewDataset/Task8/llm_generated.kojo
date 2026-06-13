clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
val triangle_side = 100


def drawPolygon(sides: Int, length: Double) {
  repeat(sides) {
    forward(length)
    right(360.0 / sides)
  }
}

drawPolygon(3, triangle_side)
right(150)
drawPolygon(3, triangle_side)
forward(triangle_side)
left(90)
forward(triangle_side)
right(120)
drawPolygon(3, triangle_side)
right(150)
drawPolygon(3, triangle_side)