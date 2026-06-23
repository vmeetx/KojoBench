clear()
setSpeed(fast)

// Draw the first semicircle on the left
right(90, 100)
penUp()
forward(100)
penDown()
left(90)
right(180, 100)

// Draw the second semicircle on the right
right(90, 100)
penUp()
forward(300)
penDown()
left(90)
right(180, 100)

// Draw the triangle below the semicircles
penUp()
forward(200)
left(90)
forward(150)
penDown()
right(120)
forward(200)
right(120)
forward(200)