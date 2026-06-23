clear()
setSpeed(fast)

// Draw the first semicircle
penDown()
forward(100)
right(90, 100)
forward(100)
right(90, 100)
penUp()

// Move to a new position for the second semicircle
hop(250, 0)

// Draw the second semicircle
penDown()
forward(100)
right(90, 100)
forward(100)
right(90, 100)
penUp()

// Move to a new position for the third semicircle
hop(-250, 0)

// Draw the third semicircle
penDown()
forward(100)
right(90, 100)
forward(100)
right(90, 100)
penUp()