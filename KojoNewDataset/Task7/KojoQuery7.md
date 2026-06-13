Draw a square with an equilateral triangle attached flush to its right side. The triangle points to the right (away from the square). The triangle's left side is exactly the square's right side — they share that edge completely. Both shapes use the same side length.

`triangle_side` specifies the side length used for both the square and the triangle in pixels. (`triangle_side = 100`)

The turtle draws the triangle first (pointing right), then turns and draws the square to the left of it. Use `setHeading(-30)` to start drawing the triangle pointing right, then turn `right(60)` before drawing the square. Use a `def drawPolygon(sides, length)` helper. Write concise Kojo code.
