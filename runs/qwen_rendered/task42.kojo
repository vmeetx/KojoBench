clear()
setSpeed(fast)

// Draw the triangle
forward(200)
right(120)
forward(200)
right(120)
forward(200)
right(120)

// Move to the starting point of the left semicircle
penUp()
setPosition(-50, 0)
penDown()

// Draw the left semicircle
left(90, 100)

// Move to the starting point of the right semicircle
penUp()
setPosition(150, 0)
penDown()

// Draw the right semicircle
right(90, 100)