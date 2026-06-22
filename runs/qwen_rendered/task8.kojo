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

// Move to the top triangle's starting point
penUp()
forward(100)
left(45)
penDown()

// Draw the top triangle
forward(141.4) // Hypotenuse of 30-60-90 triangle with base 100

// Move to the right triangle's starting point
penUp()
right(90)
forward(200)
left(135)
penDown()

// Draw the right triangle
forward(141.4)

// Move to the bottom triangle's starting point
penUp()
left(90)
forward(200)
left(135)
penDown()

// Draw the bottom triangle
forward(141.4)

// Move to the left triangle's starting point
penUp()
right(90)
forward(200)
left(135)
penDown()

// Draw the left triangle
forward(141.4)