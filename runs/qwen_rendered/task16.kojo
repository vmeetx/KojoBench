clear()
setSpeed(fast)

// Move down by 200 pixels to start at the bottom-left corner of the square
hop(200)
left(90)

// Draw the square
repeat(4) {
  forward(200)
  right(90)
}