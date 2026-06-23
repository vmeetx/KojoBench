clear()
setSpeed(fast)

// Draw the square
repeat(4) {
  forward(200)
  right(90)
}

// Move to the top-left corner and draw the circle
penUp()
forward(100)
left(90)
forward(100)
penDown()
right(90)
circle(50)

// Move to the top-right corner and draw the circle
penUp()
forward(200)
right(90)
forward(100)
penDown()
right(90)
circle(50)

// Move to the bottom-left corner and draw the circle
penUp()
forward(100)
left(90)
forward(200)
penDown()
right(90)
circle(50)

// Move to the bottom-right corner and draw the circle
penUp()
forward(200)
right(90)
forward(200)
penDown()
right(90)
circle(50)