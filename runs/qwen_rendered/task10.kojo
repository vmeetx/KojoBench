clear()
setSpeed(fast)

// Draw the square
repeat(4) {
  forward(200)
  right(90)
}

// Move to the center of the square and draw the circle
penUp()
forward(100)
left(90)
forward(100)
penDown()
right(90)
setPenColor(blue)
circle(100)