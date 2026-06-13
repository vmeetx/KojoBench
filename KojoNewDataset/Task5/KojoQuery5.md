Draw a large equilateral triangle pointing upward (flat base at the bottom), with one small equilateral triangle attached at each of its three corners. Each small triangle points OUTWARD away from the centre of the large triangle — it does not point inward or sideways. Specifically:

- At the TOP corner of the large triangle: the small triangle's own vertex points further UPWARD, and its horizontal base sits just below the tip of the large triangle.
- At the BOTTOM-LEFT corner: the small triangle's vertex points further toward the LOWER-LEFT, and its base is aligned with the lower-left side of the large triangle extended.
- At the BOTTOM-RIGHT corner: the small triangle's vertex points further toward the LOWER-RIGHT, similarly aligned.

The two sides of each small triangle are exact extensions of the two sides of the large triangle that meet at that corner. Imagine stretching each corner of the large triangle outward by `small_triangle_side` pixels: the stretched tip becomes a small triangle. The overall shape looks like a large A-shape with three small triangular "spikes" at every corner pointing away from the centre.

`large_triangle_side` specifies the side length of the central triangle in pixels. `small_triangle_side` specifies the side length of each of the three outer triangles in pixels. (`large_triangle_side = 100`, `small_triangle_side = 50`)

Use a `def drawPolygon(sides: Int, length: Double)` helper. The drawing loop runs 3 times: at each iteration, first draw the small outward triangle (using `left(60)` before and `right(60)` after to orient it outward), then turn `right(120)` and move `forward(large_triangle_side)` to reach the next corner. Start with `right(60)` before the loop. Write concise Kojo code.
