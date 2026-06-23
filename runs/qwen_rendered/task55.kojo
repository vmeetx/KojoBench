clear()
setSpeed(fast)

def drawPentagon(sideLength: Double) {
  repeat(5) {
    forward(sideLength)
    right(72)
  }
}

// Draw five concentric regular pentagons
for (i <- 0 until 5) {
  val sideLength = 200 - i * 20
  drawPentagon(sideLength)
}