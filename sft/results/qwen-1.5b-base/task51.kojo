clear()
setSpeed(fast)

// Draw the large circle
forward(100)
right(60)

// Move to the center of the large circle
forward(50)
right(120)

// Draw the small circle
forward(50)
right(60)

// Move back to the original position
forward(-50)
right(-120)

// Repeat steps 1-4 for the remaining vertices
for (i <- 1 to 5) {
  forward(100)
  right(60)
  forward(50)
  right(120)
  forward(-50)
  right(-120)
}