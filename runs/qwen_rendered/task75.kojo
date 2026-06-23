clear()
setSpeed(fast)

// Draw the outer square
repeat(4) {
  forward(100)
  right(90)
}

// Move to the center of the outer square
penUp()
forward(25)
right(90)
forward(25)
penDown()

// Rotate 45 degrees
right(45)

// Draw the inner square
repeat(4) {
  forward(70)
  right(90)
}