import unittest
from unittest.mock import patch, AsyncMock, MagicMock # AsyncMock for async functions/methods
import asyncio
import os
import subprocess # <--- IMPORT ADDED HERE

# Import the module and functions to be tested
from md2card_generator import generate_md2card, STYLES, ASPECT_RATIOS, _check_playwright_browsers, attempt_playwright_install

# Helper to run async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

class TestMd2CardGenerator(unittest.TestCase):

    # Mock _check_playwright_browsers and attempt_playwright_install as they are for CLI user experience, not core logic.
    @patch('md2card_generator._check_playwright_browsers', return_value=True) # Assume browsers are "installed" for most tests
    @patch('md2card_generator.attempt_playwright_install', new_callable=AsyncMock) # Mock the installer function
    @patch('md2card_generator.async_playwright') # Top-level patch for the playwright context manager
    @async_test
    async def test_generate_md2card_successful_flow(self, mock_async_playwright_cm, mock_attempt_install, mock_check_browsers):
        """Test successful card generation with default style and aspect ratio."""
        
        # Configure the async_playwright context manager mock
        mock_playwright_instance = AsyncMock()
        mock_async_playwright_cm.return_value.__aenter__.return_value = mock_playwright_instance
        # mock_async_playwright_cm.return_value.__aexit__.return_value = AsyncMock() # Not strictly needed unless checking specific exit behavior

        # Configure browser and page mocks
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        markdown_text = "# Hello\nTest"
        output_filename = "test_output/card.png"
        expected_width, expected_height = ASPECT_RATIOS['1:1']
        
        # Ensure output directory exists for the test
        test_dir = "test_output"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)

        await generate_md2card(markdown_text, output_filename, style='default', aspect_ratio='1:1')

        mock_playwright_instance.chromium.launch.assert_called_once()
        mock_browser.new_page.assert_called_once()
        mock_page.set_viewport_size.assert_called_once_with({"width": expected_width, "height": expected_height})
        
        self.assertTrue(mock_page.set_content.called)
        html_content_args = mock_page.set_content.call_args[0][0]
        self.assertIn("<h1>Hello</h1>", html_content_args) 
        self.assertIn("<p>Test</p>", html_content_args) 
        self.assertIn(STYLES['default'], html_content_args) 

        mock_page.screenshot.assert_called_once_with(path=output_filename, full_page=False, type='png')
        mock_browser.close.assert_called_once()
        
        if os.path.exists(output_filename):
            os.remove(output_filename)
        if os.path.exists(test_dir) and not os.listdir(test_dir): # Remove if empty
            os.rmdir(test_dir)

    @patch('md2card_generator._check_playwright_browsers', return_value=True)
    @patch('md2card_generator.attempt_playwright_install', new_callable=AsyncMock)
    @patch('md2card_generator.async_playwright')
    @async_test
    async def test_generate_md2card_custom_style_and_ratio(self, mock_async_playwright_cm, mock_attempt_install, mock_check_browsers):
        """Test with a custom style and aspect ratio."""
        mock_playwright_instance = AsyncMock()
        mock_async_playwright_cm.return_value.__aenter__.return_value = mock_playwright_instance
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        markdown_text = "Custom Card"
        output_filename = "custom_card.png" 
        style = 'dark'
        aspect_ratio = '16:9'
        expected_width, expected_height = ASPECT_RATIOS[aspect_ratio]

        await generate_md2card(markdown_text, output_filename, style=style, aspect_ratio=aspect_ratio)

        mock_page.set_viewport_size.assert_called_once_with({"width": expected_width, "height": expected_height})
        html_content_args = mock_page.set_content.call_args[0][0]
        self.assertIn("<p>Custom Card</p>", html_content_args)
        self.assertIn(STYLES[style], html_content_args)
        mock_page.screenshot.assert_called_once_with(path=output_filename, full_page=False, type='png')
        
        if os.path.exists(output_filename):
            os.remove(output_filename)

    @patch('builtins.print') 
    @async_test
    async def test_generate_md2card_empty_markdown(self, mock_print):
        await generate_md2card("", "empty.png")
        mock_print.assert_any_call("Error: Markdown text is empty or whitespace.")

    @patch('builtins.print')
    @async_test
    async def test_generate_md2card_invalid_style(self, mock_print):
        await generate_md2card("text", "invalid.png", style="nonexistent")
        mock_print.assert_any_call("Error: Invalid style 'nonexistent'. Available styles: ['default', 'dark', 'light_serif']")

    @patch('builtins.print')
    @async_test
    async def test_generate_md2card_invalid_aspect_ratio(self, mock_print):
        await generate_md2card("text", "invalid.png", aspect_ratio="10:10")
        mock_print.assert_any_call("Error: Invalid aspect ratio '10:10'. Available ratios: ['1:1', '16:9', '9:16', '4:3', '3:4']")


    @patch('md2card_generator.async_playwright')
    @async_test
    async def test_generate_md2card_playwright_browser_missing_error(self, mock_async_playwright_cm):
        """Test the specific error handling when Playwright browsers are missing."""
        mock_playwright_instance = AsyncMock()
        mock_async_playwright_cm.return_value.__aenter__.return_value = mock_playwright_instance
        
        mock_playwright_instance.chromium.launch.side_effect = Exception("Looks like Playwright Test or Playwright Library was just installed")

        with patch('builtins.print') as mock_print:
            await generate_md2card("text", "error.png")
            self.assertTrue(any("Error: Playwright browsers not found" in call.args[0] for call in mock_print.call_args_list))

    @patch('md2card_generator.os.makedirs') 
    @patch('md2card_generator.async_playwright')
    @async_test
    async def test_output_directory_creation(self, mock_async_playwright_cm, mock_makedirs):
        """Test that output directory is created if it doesn't exist."""
        mock_playwright_instance = AsyncMock()
        mock_async_playwright_cm.return_value.__aenter__.return_value = mock_playwright_instance
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_filename = "non_existent_dir/card.png"
        
        def makedirs_side_effect(path, exist_ok=False): # exist_ok for Python 3.2+
            if path == "non_existent_dir":
                pass
            else: # pragma: no cover
                os.makedirs(path, exist_ok=True) 

        mock_makedirs.side_effect = makedirs_side_effect
        
        with patch('md2card_generator.os.path.exists') as mock_path_exists:
            # First call to os.path.exists (for the dir) should be False,
            # second call (if any, for the file) can be anything or not called.
            mock_path_exists.return_value = False 

            await generate_md2card("text", output_filename)
            
            mock_path_exists.assert_called_with("non_existent_dir")
            mock_makedirs.assert_called_once_with("non_existent_dir")

        # Clean up if files/dirs were accidentally created by non-mocked parts
        if os.path.exists(output_filename): # pragma: no cover
            os.remove(output_filename)
        if os.path.exists("non_existent_dir"): # pragma: no cover
            os.rmdir("non_existent_dir")


    @patch('subprocess.run')
    def test_check_playwright_browsers_found(self, mock_subprocess_run):
        """Test _check_playwright_browsers when playwright command is found."""
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        self.assertTrue(_check_playwright_browsers())
        mock_subprocess_run.assert_called_once_with(["playwright", "--version"], check=True, capture_output=True, text=True)

    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_check_playwright_browsers_not_found_filenotfound(self, mock_subprocess_run):
        """Test _check_playwright_browsers when playwright command raises FileNotFoundError."""
        self.assertFalse(_check_playwright_browsers())

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "cmd"))
    def test_check_playwright_browsers_not_found_calledprocesserror(self, mock_subprocess_run):
        """Test _check_playwright_browsers when playwright command raises CalledProcessError."""
        self.assertFalse(_check_playwright_browsers())

    @patch('asyncio.create_subprocess_exec')
    @async_test
    async def test_attempt_playwright_install_success(self, mock_create_subprocess_exec):
        """Test attempt_playwright_install successful execution."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Success stdout", b"Success stderr")
        mock_process.returncode = 0
        mock_create_subprocess_exec.return_value = mock_process

        with patch('builtins.print') as mock_print:
            await attempt_playwright_install()
            mock_create_subprocess_exec.assert_called_once_with("playwright", "install", "--with-deps", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertTrue(any("Playwright browsers installed successfully" in call.args[0] for call in mock_print.call_args_list))

    @patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError)
    @async_test
    async def test_attempt_playwright_install_playwright_not_found(self, mock_create_subprocess_exec):
        """Test attempt_playwright_install when playwright command is not found."""
        with patch('builtins.print') as mock_print:
            await attempt_playwright_install()
            self.assertTrue(any("Error: 'playwright' command not found" in call.args[0] for call in mock_print.call_args_list))


if __name__ == '__main__':
    unittest.main()
