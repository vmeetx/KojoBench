clear()
setSpeed(fast)

// Draw the first circle
penDown()
forward(100)
right(90, 100)
forward(200)
right(90, 100)
forward(100)
right(90, 100)
penUp()

// Move to the starting position for the second circle
hop(-200, 0)

// Draw the second circle
penDown()
forward(100)
right(90, 100)
forward(200)
right(90, 100)
forward(100)
right(90, 100)
penUp()

// Draw the bounding rectangle
setPosition(-150, -100)
lineTo(150, -100)
lineTo(150, 100)
lineTo(-150, 100)
lineTo(-150, -100)