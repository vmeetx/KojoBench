clear()
setSpeed(fast)

// Function to draw an equilateral triangle with side length `side`
def drawTriangle(side: Double) {
  repeat(3) {
    forward(side)
    right(120)
  }
}

// Draw the first row of triangles
repeatFor(0 until 3) { i =>
  forward(150)
  drawTriangle(100)
  back(150)
  right(60)
}
left(180)

// Draw the second row of triangles
repeatFor(0 until 3) { i =>
  forward(150)
  drawTriangle(100)
  back(150)
  right(60)
}
left(180)

// Draw the third row of triangles
repeatFor(0 until 3) { i =>
  forward(150)
  drawTriangle(100)
  back(150)
  right(60)
}