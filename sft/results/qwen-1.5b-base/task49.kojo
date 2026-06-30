clear()
setSpeed(fast)

// Draw the four smaller circles
circle(100, 0, 0)
circle(100, 120, 0)
circle(100, -120, 0)
circle(100, 0, 120)

// Calculate the center of the larger circle
val centerX = 0 + 100 * Math.cos(Math.PI / 4)
val centerY = 0 + 100 * Math.sin(Math.PI / 4)

// Draw the larger circle
circle(200, centerX, centerY)