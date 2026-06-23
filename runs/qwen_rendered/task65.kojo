clear()
setSpeed(fast)

// Draw the first semicircle at the bottom-left corner
right(180, 100)
forward(200)
left(90, 100)
penUp()
forward(100)
penDown()
left(90)
right(180, 50)

// Draw the second semicircle above and to the right of the first
forward(300)
left(90, 100)
penUp()
forward(100)
penDown()
left(90)
right(180, 50)

// Draw the third semicircle below and to the right of the first
back(200)
right(90, 100)
penUp()
forward(100)
penDown()
left(90)
right(180, 50)