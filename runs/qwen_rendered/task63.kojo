clear()
setSpeed(fast)

// Draw the hexagon
repeat(6) {
  forward(100)
  right(60)
}

// Draw semicircles on each side of the hexagon
penUp()
forward(50)
right(90)
penDown()

for (i <- 0 until 6) {
  left(90, 50)
  right(90, 50)
  forward(100)
  right(90, 50)
  left(90, 50)
}