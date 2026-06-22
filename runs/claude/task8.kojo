clear()
setSpeed(fast)

// inner diamond (square rotated 45) corners at radius 60; outer tips at 110 diagonal
// star outline: tip -> inner corner alternating around
penUp()
setPosition(110, 110)
penDown()
lineTo(60, 0)
lineTo(110, -110)
lineTo(0, -60)
lineTo(-110, -110)
lineTo(-60, 0)
lineTo(-110, 110)
lineTo(0, 60)
lineTo(110, 110)

// inner square
penUp()
setPosition(60, 0)
penDown()
lineTo(0, 60)
lineTo(-60, 0)
lineTo(0, -60)
lineTo(60, 0)
