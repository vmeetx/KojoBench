clear()
setSpeed(fast)

// Draw the hexagon
repeat(6) {
  forward(100)
  right(60)
}

// Draw large circles at each vertex
savePosHe()
forward(50)
right(90)
penUp()
forward(20)
penDown()
circle(20)
restorePosHe()

// Draw small circles between each pair of adjacent vertices
repeat(6) {
  forward(100)
  right(60)
  savePosHe()
  forward(50)
  right(90)
  penUp()
  forward(10)
  penDown()
  circle(10)
  restorePosHe()
}