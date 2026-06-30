clear()
setSpeed(fast)

// Move to the center of the outer square
moveTo(250, 250)

// Draw the outer square
repeat(4) {
  forward(100)
  right(90)
}

// Move to the center of the inner square
moveTo(200, 200)

// Draw the inner square
repeat(4) {
  forward(50)
  right(90)
}