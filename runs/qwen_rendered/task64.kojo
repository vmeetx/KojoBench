clear()
setSpeed(fast)

// Define a function to draw an equilateral triangle with side length 100 pixels
def drawTriangle() {
  repeat(3) {
    forward(100)
    right(120)
  }
}

// Draw the first triangle
drawTriangle()

// Move to the next position and draw the second triangle
right(90)
forward(100)
left(90)
drawTriangle()

// Move to the next position and draw the third triangle
right(90)
forward(100)
left(90)
drawTriangle()

// Move to the final position and draw the fourth triangle
right(90)
forward(100)
left(90)
drawTriangle()