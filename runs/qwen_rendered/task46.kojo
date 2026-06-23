clear()
setSpeed(fast)

// Draw the first equilateral triangle
repeat(3) {
  forward(100)
  right(120)
}

// Move to the position for the second triangle
hop(150, 0)
right(90)
forward(150)
left(90)

// Draw the second equilateral triangle
repeat(3) {
  forward(100)
  right(120)
}

// Move to the position for the third triangle
hop(-150, -150)
right(90)
forward(150)
left(90)

// Draw the third equilateral triangle
repeat(3) {
  forward(100)
  right(120)
}