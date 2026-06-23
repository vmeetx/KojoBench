clear()
setSpeed(fast)

// Draw the large equilateral triangle
val sideLengthLarge = 300
repeat(3) {
  forward(sideLengthLarge)
  right(120)
}

// Move to the center of the large triangle
penUp()
forward(sideLengthLarge / 2)
left(60)
forward(sideLengthLarge * sqrt(3) / 4)
penDown()

// Draw the small equilateral triangle
val sideLengthSmall = 150
repeat(3) {
  forward(sideLengthSmall)
  right(120)
}