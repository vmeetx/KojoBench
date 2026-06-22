clear()
setSpeed(fast)

// Top half of the "S"
forward(50)
right(90, 50)
forward(100)
left(90, 50)
forward(50)

// Straight line connecting the top and bottom halves
penUp()
forward(200)
penDown()
forward(50)

// Bottom half of the "S"
right(90, 50)
forward(100)
left(90, 50)
forward(50)