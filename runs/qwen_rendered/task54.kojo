clear()
setSpeed(fast)

def drawHexagon(sideLength: Double) {
  repeat(6) {
    forward(sideLength)
    right(60)
  }
}

val hexSide = 80.0
val radius = (hexSide * math.sqrt(3)) / 2

// Draw the first hexagon at the center
drawHexagon(hexSide)

// Position and draw the remaining five hexagons in a ring
repeatFor(1 until 6) { i =>
  right(60)
  forward(radius)
  drawHexagon(hexSide)
  back(radius)
}