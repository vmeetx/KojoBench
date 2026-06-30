clear()
setSpeed(fast)

// Draw the five equally spaced sharp points
for (i <- 0 until 5) {
  forward(100)
  right(72)
}

// Draw the smaller five-sided shape formed by the intersections of the crossing lines
for (i <- 0 until 5) {
  forward(50)
  right(72)
}