#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <file.kojo>"
  exit 1
fi

input_file="$1"

if [ ! -f "$input_file" ]; then
  echo "Error: file not found: $input_file"
  exit 1
fi

base_name="$(basename "$input_file" .kojo)"
image_file="${base_name}.png"

output_dir="p1"
output_file="$output_dir/${base_name}.wrapped.kojo"

mkdir -p "$output_dir"

cat > "$output_file" <<'EOF'
package p1

object KojoHeadless {
  def main(args: Array[String]): Unit = {
    val kojo = net.kogics.kojo.lite.KojoHeadless.create()
    val builtins = kojo.builtins

    import builtins._
    import DCanvas._
    import TurtleWorld._

EOF

cat "$input_file" >> "$output_file"

cat >> "$output_file" <<EOF

    println("Exporting Kojo output...")
    exportImageToFile("$image_file")
    println("Done")
  }
}
EOF

echo "Wrote wrapped file to: $output_file"

echo "Compiling..."
scalac -cp kojo-lib-assembly-0.3.3.jar "$output_file"

echo "Running..."
scala -cp ".:kojo-lib-assembly-0.3.3.jar" p1.KojoHeadless

echo "Exported image to: $image_file"
rm -rf "$output_dir"

