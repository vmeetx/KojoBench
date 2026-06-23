clear()
setSpeed(fast)

// Draw the square
forward(200)
right(90)
forward(200)
right(90)
forward(200)
right(90)
forward(200)

// Move to the top left corner
penUp()
setPosition(0, 200)
penDown()

// Draw the diagonal from top left to bottom right
lineTo(200, 0)