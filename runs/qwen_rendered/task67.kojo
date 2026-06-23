clear()
setSpeed(fast)

// Draw top-left semicircle
penUp()
setPosition(-100, 100)
penDown()
left(90, 100)

// Draw top-right semicircle
penUp()
setPosition(100, 100)
penDown()
right(90, 100)

// Draw bottom-left semicircle
penUp()
setPosition(-100, -100)
penDown()
left(90, 100)

// Draw bottom-right semicircle
penUp()
setPosition(100, -100)
penDown()
right(90, 100)