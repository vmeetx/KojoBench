clear()
setSpeed(fast)

// Draw the rectangle
forward(200)
right(90)
forward(100)
right(90)
forward(200)
right(90)
forward(100)

// Draw the four quarter-circles
penUp()
hop(10) // Move to the top-left corner of the rectangle
setPenColor(blue)
penDown()
left(90, 20) // Quarter-circle at the top-left corner

hop(180) // Move to the top-right corner of the rectangle
right(90, 20) // Quarter-circle at the top-right corner

hop(200) // Move to the bottom-right corner of the rectangle
left(90, 20) // Quarter-circle at the bottom-right corner

hop(180) // Move to the bottom-left corner of the rectangle
right(90, 20) // Quarter-circle at the bottom-left corner