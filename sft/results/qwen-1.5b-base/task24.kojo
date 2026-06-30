clear()
setSpeed(fast)

// Draw the straight sides
forward(200) // Top side
right(90)
forward(200) // Bottom side
right(90)

// Draw the slanted side
right(45) // Slanted angle
forward(200) // Length of the slanted side
right(90)
forward(200) // Return to the starting point
right(-45) // Return to the original orientation