clear()
setSpeed(fast)

// Draw the outer pentagon
repeat(5) {
  forward(300)
  right(72)
}

// Move to the first point and draw the crossing lines
penUp()
forward(150)
right(144)
penDown()

repeat(5) {
  forward(150)
  right(144)
}