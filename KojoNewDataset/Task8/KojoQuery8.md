Draw a 4-pointed star shape: a central square with one equilateral triangle attached flush to each of its four sides, each triangle pointing outward away from the square's centre. The result looks like a compass rose or a 4-pointed star (like ✦). The square itself is fully visible — its four edges are drawn as the shared bases of the four triangles.

The four triangles point in four diagonal directions (upper-right, upper-left, lower-left, lower-right), NOT straight up/down/left/right. This is because the square is oriented at a slight angle — its sides are NOT axis-aligned. The overall outline is a symmetric 4-pointed star.

All five shapes (the central square and the four triangles) use the same side length.

`triangle_side` specifies the side length used for the square and every triangle in pixels. (`triangle_side = 100`)

Use a `def drawPolygon(sides: Int, length: Double)` helper. Start with `setHeading(-30)`. The drawing sequence is:
1. Draw a triangle (pointing right) with `drawPolygon(3, triangle_side)`
2. Turn `right(150)` and draw a second triangle (pointing up-left)
3. Move `forward(triangle_side)`, turn `left(90)`, move `forward(triangle_side)` — this traces two sides of the square
4. Turn `right(120)` and draw a third triangle, then `right(150)` and draw a fourth triangle

This traces the outline efficiently. Write concise Kojo code without a loop.
