Draw a circle inscribed perfectly inside an axis-aligned square. The square has horizontal top and bottom sides and vertical left and right sides. The circle touches each side of the square at exactly its midpoint — the circle's topmost point touches the middle of the top side, its bottommost point touches the middle of the bottom side, its leftmost point touches the middle of the left side, and its rightmost point touches the middle of the right side. There is no gap between the circle and any side.

The square's side length is exactly `2 * circle_radius`, so the circle fits snugly inside with its diameter equal to the square's side.

`circle_radius` specifies the radius of the inscribed circle in pixels — the square's side length is `2 * circle_radius`. (`circle_radius = 100`)

In Kojo, draw the circle first with `left(360, circle_radius)` starting from the bottom-left corner of the square (the turtle starts at position (0,0) which becomes the bottom-midpoint of the circle, i.e., the point where the circle touches the square's bottom side). After the circle, reposition to the bottom-left corner of the square using `left(180)` then `forward(circle_radius)` then `right(90)`, and draw the square with `drawPolygon(4, 2 * circle_radius)`. Use a `def drawPolygon(sides: Int, length: Double)` helper. Write concise Kojo code.
