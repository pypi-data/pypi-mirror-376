"""
Command Line Interface for PDF Stamper
"""

import argparse
import os
import sys
import time
from .stamper import PDFStamper, StamperConfig, Position


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Stamp PDF files with sequential numbers or custom text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf-stamper input.pdf --copies 10
  pdf-stamper input.pdf --copies 5 --prefix "K-" --output-dir ./output
  pdf-stamper input.pdf --text "CONFIDENTIAL" --position bottom-left
  pdf-stamper input.pdf --text "DRAFT" --x 100 --y 750
        """,
    )

    parser.add_argument("input_pdf", help="Input PDF file path")

    # Stamping options
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--copies", type=int, help="Number of sequential copies to generate"
    )
    group.add_argument(
        "--text", type=str, help="Custom text to stamp (alternative to --copies)"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        default="./dist",
        help="Output directory for stamped files (default: ./dist)",
    )
    parser.add_argument("--output", help="Output file path (only used with --text)")

    # Formatting options
    parser.add_argument(
        "--prefix", default="Copy", help="Prefix for sequential numbering (default: K-)"
    )
    parser.add_argument(
        "--number-format",
        default="{:03d}",
        help="Number format string (default: {:03d})",
    )

    # Position options
    parser.add_argument(
        "--position",
        choices=[pos.name.lower().replace("_", "-") for pos in Position],
        default="top-right",
        help="Predefined position for text placement (default: top-right)",
    )
    parser.add_argument(
        "--x",
        type=int,
        help="X coordinate for text placement (overrides --position if used with --y)",
    )
    parser.add_argument(
        "--y",
        type=int,
        help="Y coordinate for text placement (overrides --position if used with --x)",
    )

    parser.add_argument(
        "--font-name", default="Times-Roman", help="Font name (default: Times-Roman)"
    )
    parser.add_argument(
        "--font-size", type=int, default=13, help="Font size (default: 13)"
    )

    # Color options (RGB 0-1 range)
    parser.add_argument(
        "--text-color",
        nargs=3,
        type=float,
        default=[0.0, 0.0, 0.0],
        metavar=("R", "G", "B"),
        help="Text color as RGB values 0-1 (default: 0 0 0 for black)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file '{args.input_pdf}' does not exist.", file=sys.stderr)
        return 1

    # Validate arguments
    if not args.copies and not args.text:
        print("Error: Either --copies or --text must be specified.", file=sys.stderr)
        return 1

    # Validate position arguments
    if args.x is not None or args.y is not None:
        if args.x is None or args.y is None:
            print(
                "Error: Both --x and --y must be specified when using custom coordinates.",
                file=sys.stderr,
            )
            return 1

    if args.text and not args.output:
        # Generate default output name
        base_name = os.path.splitext(os.path.basename(args.input_pdf))[0]
        args.output = f"{base_name}_stamped.pdf"

    # Determine position coordinates
    if args.x is not None and args.y is not None:
        # Use custom coordinates
        position = (args.x, args.y)
    else:
        # Use predefined position
        position_name = args.position.upper().replace("-", "_")
        position = Position[position_name].value

    # Create stamper instance with configuration
    config = StamperConfig(
        font_name=args.font_name,
        font_size=args.font_size,
        text_color=tuple(args.text_color),
        position=position,
        prefix=args.prefix,
        number_format=args.number_format,
    )
    stamper = PDFStamper(config=config)

    try:
        if args.copies:
            # Generate multiple copies
            if args.verbose:
                print(f"Generating {args.copies} stamped copies...")
                print(f"Input: {args.input_pdf}")
                print(f"Output directory: {os.path.abspath(args.output_dir)}")
                print(f"Prefix: {args.prefix}")
                if args.x is not None and args.y is not None:
                    print(f"Position: custom {position}")
                else:
                    print(f"Position: {args.position} {position}")

            start_time = time.time()

            output_files = stamper.stamp_multiple_copies(
                input_pdf_path=args.input_pdf,
                output_dir=args.output_dir,
                num_copies=args.copies,
            )

            total_time = time.time() - start_time

            if args.verbose:
                print(
                    f"\nCompleted! Generated {args.copies} copies in {total_time:.2f} seconds"
                )
                print(f"Average time per copy: {total_time/args.copies:.2f} seconds")
                print("Output files:")
                for output_file in output_files:
                    print(f"  {output_file}")
            else:
                print(f"Generated {args.copies} stamped copies in {args.output_dir}")

        else:
            # Single text stamp
            if args.verbose:
                print(f"Stamping PDF with text: '{args.text}'")
                print(f"Input: {args.input_pdf}")
                print(f"Output: {args.output}")
                if args.x is not None and args.y is not None:
                    print(f"Position: custom {position}")
                else:
                    print(f"Position: {args.position} {position}")

            stamper.stamp_pdf(
                input_pdf_path=args.input_pdf,
                output_pdf_path=args.output,
                text=args.text,
            )

            if args.verbose:
                print("Stamping completed successfully!")
            else:
                print(f"Stamped PDF saved as: {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
