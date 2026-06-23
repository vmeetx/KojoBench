clear()
setSpeed(fast)

// Draw the first large triangle
repeat(3) {
  forward(200)
  right(120)
}

// Move to a position for the smaller triangle
penUp()
forward(100)
right(60)
forward(100 * Math.sqrt(3))
left(120)
penDown()

// Draw the smaller triangle
repeat(3) {
  forward(100)
  right(120)
}

// Move back to the starting point of the first large triangle
penUp()
right(60)
forward(100 * Math.sqrt(3))
left(120)
forward(200)
penDown()

// Draw the second large triangle
repeat(3) {
  forward(200)
  right(120)
}