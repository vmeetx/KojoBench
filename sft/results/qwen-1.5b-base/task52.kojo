clear()
setSpeed(fast)

// Move to center of square 1
moveTo(250, 250)

// Rotate square 2 45 degrees around its center
rotate(45)

// Move back to center of square 1
moveTo(250, 250)

// Draw lines connecting corresponding vertices of the two squares
lineTo(250 + 100 * cos(45), 250 - 100 * sin(45))
lineTo(250 + 100 * cos(135), 250 - 100 * sin(135))
lineTo(250 + 100 * cos(225), 250 - 100 * sin(225))
lineTo(250 + 100 * cos(315), 250 - 100 * sin(315))
lineTo(250 + 100 * cos(45), 250 - 100 * sin(45))
lineTo(250 + 100 * cos(135), 250 - 100 * sin(135))
lineTo(250 + 100 * cos(225), 250 - 100 * sin(225))
lineTo(250 + 100 * cos(315), 250 - 100 * sin(315))