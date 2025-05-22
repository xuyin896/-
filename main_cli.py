import argparse
import asyncio
import json
import os

# Attempt to import from other modules
try:
    from text_processor import process_text_to_structure
except ImportError:
    print("Error: text_processor.py not found or process_text_to_structure could not be imported.")
    process_text_to_structure = None

try:
    from mindmap_generator import generate_mindmap
except ImportError:
    print("Error: mindmap_generator.py not found or generate_mindmap could not be imported.")
    generate_mindmap = None

try:
    from md2card_generator import generate_md2card, ASPECT_RATIOS as md2card_aspect_ratios, STYLES as md2card_styles
except ImportError:
    print("Error: md2card_generator.py not found or its components could not be imported.")
    generate_md2card = None
    md2card_aspect_ratios = {'1:1': (100,100)} # Dummy for parser setup
    md2card_styles = {'default': ""} # Dummy for parser setup

def ensure_output_dir_exists(filepath: str):
    """Ensures the output directory for the given filepath exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created output directory: {directory}")
        except OSError as e:
            print(f"Error creating output directory {directory}: {e}")
            # Depending on severity, might want to raise or exit
            return False 
    return True

def load_text_input(input_source: str) -> str:
    """Loads text from a file if input_source is a path, otherwise returns it as is."""
    if os.path.isfile(input_source):
        try:
            with open(input_source, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {input_source}: {e}")
            return None
    return input_source # It's a string already

def load_json_input(input_source: str) -> dict:
    """Loads JSON from a file or parses a JSON string."""
    if not input_source:
        return None
    if os.path.isfile(input_source):
        try:
            with open(input_source, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading or parsing JSON file {input_source}: {e}")
            return None
    else:
        try:
            return json.loads(input_source)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON string: {e}")
            print("JSON string provided:", input_source[:100] + "..." if len(input_source) > 100 else input_source)
            return None


def handle_mindmap_command(args):
    print("Executing mindmap command...")
    if not process_text_to_structure or not generate_mindmap:
        print("Mindmap generation dependencies are missing. Cannot proceed.")
        return

    text_content = load_text_input(args.text)
    if text_content is None:
        return # Error already printed by load_text_input

    if not ensure_output_dir_exists(args.output):
        return

    style_attributes = None
    if args.style:
        style_attributes = load_json_input(args.style)
        if style_attributes is None:
            print("Proceeding with default mindmap style due to style parsing error.")
            # No return, proceed with default style

    print(f"Processing text for mind map structure...")
    structured_data = process_text_to_structure(text_content)

    if not structured_data:
        print("Text processing resulted in empty structure. Mind map will not be generated.")
        return

    print(f"Generating mind map to {args.output}...")
    generate_mindmap(structured_data, args.output, style_attributes=style_attributes)
    # generate_mindmap should print its own success/failure message


def handle_md2card_command(args):
    print("Executing md2card command...")
    if not generate_md2card:
        print("md2card generation dependencies are missing. Cannot proceed.")
        return

    markdown_content = load_text_input(args.markdown)
    if markdown_content is None:
        return # Error already printed by load_text_input
    
    if not ensure_output_dir_exists(args.output):
        return

    print(f"Generating md2card to {args.output} with style '{args.style}' and aspect ratio '{args.aspect_ratio}'...")
    
    # asyncio.run() is suitable for top-level entry points
    asyncio.run(generate_md2card(
        markdown_text=markdown_content,
        output_filename=args.output,
        style=args.style,
        aspect_ratio=args.aspect_ratio
    ))
    # generate_md2card should print its own success/failure message


def main():
    parser = argparse.ArgumentParser(description="Generate mind maps or Markdown cards from text.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Mindmap sub-command parser
    mindmap_parser = subparsers.add_parser("mindmap", help="Generate a mind map from text.")
    mindmap_parser.add_argument(
        "--text", 
        type=str, 
        required=True,
        help="Input text string or path to a .txt file."
    )
    mindmap_parser.add_argument(
        "--output", 
        type=str, 
        required=True,
        help="Output filename for the mind map image (e.g., mindmap.png)."
    )
    mindmap_parser.add_argument(
        "--style", 
        type=str, 
        required=False,
        help="Optional: JSON string or path to a JSON file for Graphviz style attributes."
    )
    mindmap_parser.set_defaults(func=handle_mindmap_command)

    # md2card sub-command parser
    md2card_parser = subparsers.add_parser("md2card", help="Generate an image card from Markdown text.")
    md2card_parser.add_argument(
        "--markdown", 
        type=str, 
        required=True,
        help="Input Markdown string or path to a .md file."
    )
    md2card_parser.add_argument(
        "--output", 
        type=str, 
        required=True,
        help="Output filename for the card image (e.g., card.png)."
    )
    md2card_parser.add_argument(
        "--style", 
        type=str, 
        choices=list(md2card_styles.keys()) if md2card_styles else ['default'], 
        default='default',
        help=f"Choose card style. Defaults to 'default'. Available: {', '.join(list(md2card_styles.keys()) if md2card_styles else ['default'])}"
    )
    md2card_parser.add_argument(
        "--aspect-ratio", 
        type=str, 
        choices=list(md2card_aspect_ratios.keys()) if md2card_aspect_ratios else ['1:1'],
        default='1:1',
        help=f"Choose card aspect ratio. Defaults to '1:1'. Available: {', '.join(list(md2card_aspect_ratios.keys()) if md2card_aspect_ratios else ['1:1'])}"
    )
    md2card_parser.set_defaults(func=handle_md2card_command)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This case should not be reached if subparsers are 'required'
        parser.print_help()

if __name__ == '__main__':
    # Check if dependencies are met before running main, or let main handle it.
    # For now, letting main print errors from imports.
    main()
