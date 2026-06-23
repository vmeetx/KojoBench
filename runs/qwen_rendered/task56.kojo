clear()
setSpeed(fast)

// Draw the first hexagon at the bottom center
def drawHexagon(sideLength: Double) {
  repeat(6) {
    forward(sideLength)
    right(60)
  }
}

drawHexagon(100)

// Move to the position for the second hexagon
penUp()
forward(50 * math.sqrt(3))
right(60)
forward(50)
left(60)
penDown()

// Draw the second hexagon
drawHexagon(100)

// Move to the position for the third hexagon
penUp()
back(100)
right(60)
forward(50 * math.sqrt(3))
left(60)
penDown()

// Draw the third hexagon
drawHexagon(100)