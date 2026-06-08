package p1

object KojoHeadless {
  def main(args: Array[String]): Unit = {
    val kojo = net.kogics.kojo.lite.KojoHeadless.create()
    val builtins = kojo.builtins

    import builtins._
    import DCanvas._
    import TurtleWorld._

clear()
setSpeed(fast)
val small_hexagon_side = 100
setHeading(0)
def draw_polygon(sides: Int, length: Double) {
  var outer_turn = 360 / sides
  repeat(sides.toInt) {
    forward(length)
    right(outer_turn)
  }
}
repeat(6) {
  draw_polygon(6, small_hexagon_side)
  right(60)
}
    println("Exporting Kojo output...")
    exportImageToFile("_render_4c90a849.png")
    println("Done")
  }
}
