clear()
setSpeed(fast)

// Draw the square
repeat(4) {
  forward(100)
  right(90)
}

// Move to the starting position for the first quarter-circle
penUp()
forward(50)
right(90)
forward(50)
penDown()

// Draw the top-left quarter-circle
left(90, 50)

// Move to the starting position for the second quarter-circle
penUp()
forward(100)
penDown()

// Draw the top-right quarter-circle
right(90, 50)

// Move to the starting position for the third quarter-circle
penUp()
forward(100)
left(180)
penDown()

// Draw the bottom-right quarter-circle
left(90, 50)

// Move to the starting position for the fourth quarter-circle
penUp()
forward(100)
right(180)
penDown()

// Draw the bottom-left quarter-circle
right(90, 50)