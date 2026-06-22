clear()
setSpeed(fast)

// Draw the flat side
forward(200)

// Move to the starting point for the first arc
penUp()
back(100)
right(90)
forward(50)
left(90)
penDown()

// Draw the first arc
right(180, 50)

// Move to the starting point for the second arc
penUp()
forward(200)
right(90)
forward(50)
left(90)
penDown()

// Draw the second arc
left(180, 50)