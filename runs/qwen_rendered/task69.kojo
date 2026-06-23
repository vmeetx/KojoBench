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
right(90)

// Draw the semicircle at the top-left corner
penUp()
setPosition(-100, 100)
penDown()
left(90, 100)

// Draw the semicircle at the top-right corner
penUp()
setPosition(100, 100)
penDown()
right(90, 100)

// Draw the semicircle at the bottom-left corner
penUp()
setPosition(-100, -100)
penDown()
left(90, 100)

// Draw the semicircle at the bottom-right corner
penUp()
setPosition(100, -100)
penDown()
right(90, 100)