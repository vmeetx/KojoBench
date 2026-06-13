Draw an S-shape made of two semicircles joined by a straight vertical line. The image looks exactly like the letter S (or a figure-8 cut in half).

The shape has three components drawn in one continuous stroke:
1. A top semicircle whose curved arc bulges to the RIGHT. Its flat diameter side is a vertical line segment on the LEFT. The arc starts at the top of this diameter and sweeps rightward, ending at the bottom of this diameter.
2. A bottom semicircle whose curved arc bulges to the LEFT. Its flat diameter side is a vertical line segment on the RIGHT. The arc starts at the top of this diameter and sweeps leftward, ending at the bottom.
3. A single straight vertical line running from the very TOP of the shape to the very BOTTOM — this is the shared spine of both semicircles. Its total length is 4 × radius (two stacked diameters).

The two semicircles connect at the MID-POINT of the vertical spine. The top semicircle occupies the upper half, curving RIGHT. The bottom semicircle occupies the lower half, curving LEFT. The straight line passes through both of their flat diameter sides.

`semicircle_radius` specifies the radius of each semicircle in pixels — the diameter of each semicircle, and therefore the length of each half of the vertical spine, is `2 * semicircle_radius`. (`semicircle_radius = 70`)

In Kojo: `right(180, r)` draws a rightward-curving semicircle arc, and `left(180, r)` draws a leftward-curving one. The turtle starts heading West (`setHeading(180)`). Draw the top semicircle with `right(180, semicircle_radius)`, then the bottom semicircle with `left(180, semicircle_radius)`, then turn `left(90)` and go `forward(4 * semicircle_radius)` to draw the vertical spine. Write short, simple Kojo code — no helper needed.
