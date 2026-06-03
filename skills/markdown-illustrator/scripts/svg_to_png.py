import os
import sys
import subprocess
import shutil

def convert_svg_to_png(svg_path, png_path, width=None):
    # Ensure parent directory of png_path exists
    png_dir = os.path.dirname(png_path)
    if png_dir and not os.path.exists(png_dir):
        os.makedirs(png_dir, exist_ok=True)

    is_windows = os.name == "nt"

    # 1. Try using npx @resvg/resvg-js-cli (Rust-based, very fast and accurate)
    npx_path = shutil.which("npx")
    if npx_path:
        cmd = ["npx", "-y", "@resvg/resvg-js-cli", svg_path, png_path]
        if width:
            cmd.extend(["--fit-width", str(width)])
        print(f"Trying npx resvg: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=is_windows)
            print("Successfully converted using resvg-js-cli via npx.")
            print(f"[AGENT GUIDANCE]\nSUCCESS. Converted SVG to PNG at {png_path}.", file=sys.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print(f"npx resvg failed: {e.stderr}")
            # Fall through to next method

    # 2. Try rsvg-convert (common on Linux/Unix systems)
    rsvg_path = shutil.which("rsvg-convert")
    if rsvg_path:
        cmd = ["rsvg-convert"]
        if width:
            cmd.extend(["-w", str(width)])
        cmd.extend(["-o", png_path, svg_path])
        print(f"Trying rsvg-convert: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, shell=is_windows)
            print("Successfully converted using rsvg-convert.")
            print(f"[AGENT GUIDANCE]\nSUCCESS. Converted SVG to PNG at {png_path}.", file=sys.stderr)
            return True
        except Exception as e:
            print(f"rsvg-convert failed: {e}")
            # Fall through

    # 3. Try inkscape (vector editor with CLI support)
    inkscape_path = shutil.which("inkscape")
    if inkscape_path:
        cmd = ["inkscape", svg_path, "-o", png_path]
        if width:
            cmd.extend(["-w", str(width)])
        print(f"Trying inkscape: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, shell=is_windows)
            print("Successfully converted using Inkscape.")
            print(f"[AGENT GUIDANCE]\nSUCCESS. Converted SVG to PNG at {png_path}.", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Inkscape failed: {e}")
            # Fall through

    print("[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
          "Could not find any SVG rendering tool (npx/resvg-js-cli, rsvg-convert, inkscape).\n"
          "ACTION:\n"
          "1. Install NodeJS (for npx), librsvg (for rsvg-convert), or Inkscape to enable conversion.\n"
          "2. Alternatively, keep the .svg file and embed it directly in the document, as web browsers render SVGs natively.", file=sys.stderr)
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python svg_to_png.py <input.svg> <output.png> [width]")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    png_file = sys.argv[2]
    width_val = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = convert_svg_to_png(svg_file, png_file, width_val)
    sys.exit(0 if success else 1)
