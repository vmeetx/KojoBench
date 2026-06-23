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

// Move to the starting point of the diagonal
penUp()
setPosition(100, 400)
penDown()

// Draw the diagonal
lineTo(300, 100)