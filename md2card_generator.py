import asyncio
import markdown
from playwright.async_api import async_playwright
import os
import subprocess # For attempting playwright install

BASE_WIDTH = 1080  # Base width for 1:1 aspect ratio

ASPECT_RATIOS = {
    '1:1': (BASE_WIDTH, BASE_WIDTH),
    '16:9': (1920, 1080), # Standard HD, width is dominant
    '9:16': (1080, 1920), # Portrait, height is dominant
    '4:3': (1440, 1080), # Common presentation ratio, adjust width for 1080 height
    '3:4': (1080, 1440)  # Portrait version of 4:3
}

STYLES = {
    'default': """
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh; /* Full viewport height */
            overflow: hidden; /* Prevent scrollbars on body */
        }
        .card-content {
            padding: 40px;
            box-sizing: border-box;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center; /* Center content vertically */
            align-items: center; /* Center content horizontally */
            text-align: center; /* Center text within its own block */
            overflow-wrap: break-word; /* Wrap long words */
            word-wrap: break-word; /* Older browsers */
        }
        .card-content h1, .card-content h2, .card-content h3 { color: #0056b3; }
        .card-content ul, .card-content ol { text-align: left; display: inline-block; }
        .card-content img { max-width: 90%; max-height: 40%; object-fit: contain; margin-top: 10px; }
    """,
    'dark': """
        body {
            font-family: Arial, sans-serif;
            background-color: #2c3e50; /* Dark blue-gray */
            color: #ecf0f1; /* Light silver */
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }
        .card-content {
            padding: 40px;
            box-sizing: border-box;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .card-content h1, .card-content h2, .card-content h3 { color: #3498db; } /* Bright blue */
        .card-content a { color: #3498db; }
        .card-content ul, .card-content ol { text-align: left; display: inline-block; }
        .card-content img { max-width: 90%; max-height: 40%; object-fit: contain; margin-top: 10px; filter: brightness(0.9) contrast(1.1); }
    """,
    'light_serif': """
        body {
            font-family: 'Georgia', serif;
            background-color: #faf3e0; /* Creamy background */
            color: #5a3e2b; /* Brown text */
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }
        .card-content {
            padding: 50px;
            box-sizing: border-box;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .card-content h1, .card-content h2, .card-content h3 { color: #cb4b16; } /* Solarized Orange */
        .card-content a { color: #268bd2; } /* Solarized Blue */
        .card-content ul, .card-content ol { text-align: left; display: inline-block; }
         .card-content img { max-width: 90%; max-height: 40%; object-fit: contain; margin-top: 10px; border: 1px solid #eee; }
    """
}

def _check_playwright_browsers():
    """
    Checks if Playwright browsers are likely installed.
    This is a heuristic check. A more robust check would involve
    trying to launch a browser, but that's too slow for a quick check.
    The `playwright.driver_path` might exist even if browsers are not installed.
    A common indicator is the presence of browser directories in Playwright's cache.
    However, the most user-friendly approach is to try and catch the error upon launch.
    """
    # For now, this function is a placeholder. The actual check is best done by attempting
    # to launch and catching the specific error, or by relying on the user to have run `playwright install`.
    # A simple check could be looking for playwright's CLI existence, but not browser presence.
    try:
        # This doesn't guarantee browsers are installed, just that playwright CLI is likely available.
        subprocess.run(["playwright", "--version"], check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

async def generate_md2card(markdown_text: str, output_filename: str, style: str = 'default', aspect_ratio: str = '1:1'):
    """
    Generates an image card from Markdown text.

    Args:
        markdown_text: The Markdown content for the card.
        output_filename: The filename for the output image (e.g., 'card.png').
        style: The CSS style theme to use ('default', 'dark', 'light_serif').
        aspect_ratio: The aspect ratio for the card ('1:1', '16:9', '9:16', '4:3', '3:4').

    Playwright Browser Installation:
        This function requires Playwright browsers to be installed. If they are not,
        Playwright will raise an error during browser launch. Typically, you run
        `playwright install` once from your terminal to download them.
        The `if __name__ == '__main__':` block in this script attempts a one-time install
        if browsers seem missing when the script is run directly.
    """
    if not markdown_text or markdown_text.isspace():
        print("Error: Markdown text is empty or whitespace.")
        return

    if style not in STYLES:
        print(f"Error: Invalid style '{style}'. Available styles: {list(STYLES.keys())}")
        return

    if aspect_ratio not in ASPECT_RATIOS:
        print(f"Error: Invalid aspect ratio '{aspect_ratio}'. Available ratios: {list(ASPECT_RATIOS.keys())}")
        return

    width, height = ASPECT_RATIOS[aspect_ratio]
    css_style = STYLES[style]
    html_content = markdown.markdown(markdown_text, extensions=['extra', 'nl2br'])

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-A">
        <style>
            {css_style}
        </style>
    </head>
    <body>
        <div class="card-content">
            {html_content}
        </div>
    </body>
    </html>
    """

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": width, "height": height})
            await page.set_content(full_html)
            
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            await page.screenshot(path=output_filename, full_page=False, type='png') # Capture viewport
            print(f"Card generated successfully: {output_filename} ({width}x{height}, style: {style})")

        except Exception as e:
            if "Looks like Playwright Test or Playwright Library was just installed" in str(e) or \
               "Executable doesn't exist" in str(e):
                print("Error: Playwright browsers not found or not installed correctly.")
                print("Please run 'playwright install' in your terminal.")
                print("If running this script directly, it will attempt to install them now (one-time).")
                # This error might also appear if the browser launch fails for other reasons.
            else:
                print(f"An error occurred during card generation: {e}")
        finally:
            if browser:
                await browser.close()

async def attempt_playwright_install():
    """Attempts to run playwright install if browsers seem missing."""
    print("Attempting to install Playwright browsers. This might take a few minutes...")
    try:
        process = await asyncio.create_subprocess_exec(
            "playwright", "install", "--with-deps", # --with-deps for system dependencies on Linux
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            print("Playwright browsers installed successfully (or were already installed).")
            print("Please re-run the script to generate cards.")
        else:
            print("Error installing Playwright browsers:")
            print("STDOUT:", stdout.decode() if stdout else "N/A")
            print("STDERR:", stderr.decode() if stderr else "N/A")
            print("Please try running 'playwright install --with-deps' manually in your terminal.")
    except FileNotFoundError:
        print("Error: 'playwright' command not found. Is Playwright installed correctly (pip install playwright)?")
    except Exception as e:
        print(f"An unexpected error occurred during Playwright browser installation: {e}")

if __name__ == '__main__':
    async def main():
        # Check if browsers are installed, if not, try to install them.
        # This is a simplified check; Playwright's own error on launch is more definitive.
        try:
            async with async_playwright() as p_check:
                await p_check.chromium.launch() # Quick check if browser can launch
        except Exception:
            print("Playwright browsers might be missing or launch failed.")
            await attempt_playwright_install()
            # Exit after attempting install, user should re-run.
            print("Exiting. Please re-run the script if installation was successful.")
            return

        print("Generating example cards...")

        # Example 1: Simple text, default style, 1:1
        await generate_md2card(
            markdown_text="Hello, World!\nThis is a simple card.",
            output_filename="output_cards/card_default_1_1.png",
            style="default",
            aspect_ratio="1:1"
        )

        # Example 2: Heading and paragraph, dark style, 16:9
        await generate_md2card(
            markdown_text="# Important Announcement\n\nThis is a test of the dark theme with a 16:9 aspect ratio.",
            output_filename="output_cards/card_dark_16_9.png",
            style="dark",
            aspect_ratio="16:9"
        )

        # Example 3: List, light_serif style, 9:16
        await generate_md2card(
            markdown_text="## My Tasks\n\n*   Task 1\n*   Task 2\n*   Task 3 - this is a longer task item to see how text wrapping behaves within the card.",
            output_filename="output_cards/card_light_serif_9_16.png",
            style="light_serif",
            aspect_ratio="9:16"
        )

        # Example 4: Markdown with an image, default style, 4:3
        # (Assuming a placeholder image, actual image rendering depends on accessibility from Playwright's browser)
        # For local testing, you might use a file:/// URL if the image is local and accessible.
        # For this example, using a common placeholder service.
        md_with_image = (
            "## Card with Image\n\n"
            "This card includes an image below.\n\n"
            "![Placeholder Image](https://via.placeholder.com/300x150.png?text=Sample+Image)"
        )
        await generate_md2card(
            markdown_text=md_with_image,
            output_filename="output_cards/card_image_4_3.png",
            style="default",
            aspect_ratio="4:3"
        )
        
        # Example 5: More complex content, dark style, 3:4
        complex_md = """
# Data Science Report

## Key Findings
- **Insight A:** Discovered a new trend.
- **Insight B:** Confirmed hypothesis X.

### Sub-section
Details about the methodology used.

```python
# Sample code
def hello():
    print("Hello from Markdown!")
```
        """
        await generate_md2card(
            markdown_text=complex_md,
            output_filename="output_cards/card_complex_dark_3_4.png",
            style="dark",
            aspect_ratio="3:4"
        )

        # Example 6: Empty markdown (should print error)
        print("\nTesting with empty markdown (expecting error message):")
        await generate_md2card("", "output_cards/card_empty.png")

        # Example 7: Invalid style (should print error)
        print("\nTesting with invalid style (expecting error message):")
        await generate_md2card("Test", "output_cards/card_invalid_style.png", style="nonexistent_style")

        # Example 8: Invalid aspect ratio (should print error)
        print("\nTesting with invalid aspect ratio (expecting error message):")
        await generate_md2card("Test", "output_cards/card_invalid_ratio.png", aspect_ratio="10:10")

    asyncio.run(main())
