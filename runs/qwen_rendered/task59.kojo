clear()
setSpeed(fast)

// Draw the large square
forward(400)
right(90)
forward(400)
right(90)
forward(400)
right(90)
forward(400)
right(90)

// Position and draw the four smaller squares
penUp()
forward(100)
left(90)
forward(100)
penDown()

repeat(2) {
  forward(100)
  right(90)
  forward(100)
  right(90)
}

penUp()
right(90)
forward(200)
penDown()

repeat(2) {
  forward(100)
  right(90)
  forward(100)
  right(90)
}

penUp()
left(90)
forward(300)
penDown()

repeat(2) {
  forward(100)
  right(90)
  forward(100)
  right(90)
}