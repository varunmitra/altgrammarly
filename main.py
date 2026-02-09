"""
AltGrammarly - A macOS menu bar grammar assistant powered by Gemini API.
"""
import os
import sys
import time
import threading
import logging
from pathlib import Path

import rumps
import pyperclip
from pynput import keyboard
from dotenv import load_dotenv, set_key, find_dotenv
from AppKit import NSAlert, NSAlertFirstButtonReturn, NSTextField, NSMakeRect

from gemini_client import GeminiClient
from context_utils import get_active_window_info, get_persona_for_app, get_context_aware_instruction


# Setup logging to file
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'altgrammarly.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # Write mode to clear on each start
        logging.StreamHandler(sys.stdout)  # Also print to console if running in terminal
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("=" * 60)
logger.info("AltGrammarly Starting...")
logger.info(f"Log file: {log_file}")
logger.info("=" * 60)


class AltGrammarlyApp(rumps.App):
    """macOS menu bar application for grammar and style assistance."""
    
    def __init__(self):
        logger.info("Initializing AltGrammarly application...")
        super(AltGrammarlyApp, self).__init__(
            name="AltGrammarly",
            icon=None,  # No icon for now; you can add a .png/.icns file later
            quit_button=None  # We'll create our own quit button
        )
        logger.info("Menu bar app initialized")
        
        # Initialize Gemini client
        logger.info("Initializing Gemini client...")
        self.gemini_client = GeminiClient(model_id='gemini-2.5-flash')
        if self.gemini_client.is_configured():
            logger.info("✓ Gemini API key is configured")
        else:
            logger.warning("⚠ Gemini API key is NOT configured")
        
        # State tracking
        self.is_processing = False
        self.current_operation = None  # Track which operation is running
        
        # Context tracking
        self.current_context = None  # Store active window info
        self.context_menu_item = None  # Will hold reference to context menu item
        
        # Setup menu items
        self.setup_menu()
        logger.info("Menu items configured")
        
        # Start hotkey listener in a separate thread
        logger.info("Starting hotkey listener thread (Cmd+Shift+G)...")
        self.listener_thread = threading.Thread(target=self.start_hotkey_listener, daemon=True)
        self.listener_thread.start()
        logger.info("✓ Hotkey listener thread started")
        logger.info("=" * 60)
        logger.info("App is ready! Waiting for hotkey press (Cmd+Shift+G)...")
        logger.info("=" * 60)
    
    def setup_menu(self):
        """Setup menu bar items."""
        # API Key status
        if self.gemini_client.is_configured():
            status_item = rumps.MenuItem("✓ API Key Configured", callback=None)
        else:
            status_item = rumps.MenuItem("⚠ API Key Not Set", callback=None)
        
        # Context display (disabled, updated by timer)
        self.context_menu_item = rumps.MenuItem("Context: Detecting...", callback=None)
        
        # Menu items
        self.menu = [
            status_item,
            self.context_menu_item,
            None,  # Separator
            rumps.MenuItem("🪄 Magic Action", callback=self.magic_action),
            None,  # Separator
            rumps.MenuItem("Set Gemini API Key", callback=self.set_api_key),
            rumps.MenuItem("Test Connection", callback=self.test_connection),
            None,  # Separator
            rumps.MenuItem("View Logs", callback=self.view_logs),
            rumps.MenuItem("Hotkeys:", callback=None),  # Header
            rumps.MenuItem("  ⌃⌘0 - Magic (Context)", callback=None),
            rumps.MenuItem("  ⌃⌘1 - Correct", callback=None),
            rumps.MenuItem("  ⌃⌘2 - Shorten", callback=None),
            rumps.MenuItem("  ⌃⌘3 - Rephrase", callback=None),
            rumps.MenuItem("  ⌃⌘4 - Formal", callback=None),
            rumps.MenuItem("  ⌃⌘5 - Respectful", callback=None),
            rumps.MenuItem("  ⌃⌘6 - Positive", callback=None),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
    
    @rumps.timer(2)
    def update_context(self, _):
        """Timer callback to update context display every 2 seconds."""
        try:
            window_info = get_active_window_info()
            
            if window_info:
                app_name = window_info.get('app_name', 'Unknown')
                persona = get_persona_for_app(app_name)
                
                # Update the stored context
                self.current_context = {
                    'app_name': app_name,
                    'persona': persona
                }
                
                # Update menu item
                if persona:
                    self.context_menu_item.title = f"Context: {app_name} ({persona})"
                else:
                    self.context_menu_item.title = f"Context: {app_name}"
                    
                logger.debug(f"Context updated: {app_name} -> {persona}")
            else:
                self.context_menu_item.title = "Context: Unable to detect"
                self.current_context = None
                
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            self.context_menu_item.title = "Context: Error"
    
    def magic_action(self, _):
        """
        Magic Action: Intelligently process clipboard content based on active app context.
        Detects the active app, applies the appropriate persona, and processes the text.
        """
        logger.info("=" * 60)
        logger.info("MAGIC ACTION TRIGGERED")
        logger.info("=" * 60)
        
        if self.is_processing:
            logger.warning("Already processing another request")
            self.show_notification("Busy", "Please wait for the current operation to complete.")
            return
        
        if not self.gemini_client.is_configured():
            logger.error("API key not configured")
            self.show_notification("Error", "Please configure your Gemini API key first.")
            return
        
        # Run in separate thread to not block UI
        threading.Thread(target=self._magic_action_worker, daemon=True).start()
    
    def _magic_action_worker(self):
        """Worker thread for magic action processing."""
        self.is_processing = True
        
        try:
            # Step 1: Get active window context
            logger.info("Step 1: Detecting active window context...")
            window_info = get_active_window_info()
            
            if window_info:
                app_name = window_info.get('app_name', 'Unknown')
                persona = get_persona_for_app(app_name)
                logger.info(f"✓ Active app: {app_name}")
                logger.info(f"✓ Persona: {persona or 'None (using default)'}")
            else:
                app_name = "Unknown"
                persona = None
                logger.warning("⚠ Could not detect active window, using default instruction")
            
            # Step 2: Get clipboard content
            logger.info("Step 2: Reading clipboard content...")
            original_text = pyperclip.paste()
            
            if not original_text or not original_text.strip():
                logger.warning("No text in clipboard")
                self.show_notification("No Text", "Please copy some text to clipboard first.")
                return
            
            logger.info(f"✓ Clipboard content: {len(original_text)} characters")
            logger.info(f"Text preview: '{original_text[:100]}{'...' if len(original_text) > 100 else ''}'")
            
            # Step 3: Prepare context-aware instruction
            logger.info("Step 3: Preparing context-aware instruction...")
            
            # Use grammar correction as base instruction
            from gemini_client import InstructionPresets
            base_instruction = InstructionPresets.GRAMMAR_CORRECTION
            
            if persona:
                # Enhance with persona
                enhanced_instruction = f"You are a {persona}. {base_instruction}"
                logger.info(f"✓ Enhanced instruction with persona: {persona}")
            else:
                enhanced_instruction = base_instruction
                logger.info("✓ Using base instruction (no persona enhancement)")
            
            # Step 4: Process with Gemini
            logger.info("Step 4: Processing with Gemini API...")
            processed_text = self.gemini_client.process(
                original_text,
                enhanced_instruction,
                operation=f"magic action ({app_name})"
            )
            
            logger.info(f"✓ Received processed text ({len(processed_text)} chars)")
            logger.info(f"Processed preview: '{processed_text[:100]}{'...' if len(processed_text) > 100 else ''}'")
            
            # Step 5: Update clipboard
            logger.info("Step 5: Updating clipboard with processed text...")
            pyperclip.copy(processed_text)
            logger.info("✓ Clipboard updated")
            
            # Success notification
            logger.info("=" * 60)
            logger.info(f"MAGIC ACTION COMPLETE for {app_name}")
            logger.info("=" * 60)
            
            notification_msg = f"Processed for {app_name}"
            if persona:
                notification_msg += f" ({persona})"
            
            self.show_notification("Magic Action Complete! ✨", notification_msg)
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            self.show_notification("Configuration Error", str(e))
        except Exception as e:
            logger.error(f"Error during magic action: {e}", exc_info=True)
            self.show_notification("Error", f"Failed to process: {str(e)}")
        finally:
            self.is_processing = False
            logger.info("Magic action workflow complete.")
    
    def start_hotkey_listener(self):
        """Start listening for global hotkeys (Ctrl+Cmd+1 through 6)."""
        logger.info("Hotkey listener: Setting up keyboard listener...")
        
        # Track currently pressed keys
        current_keys = set()
        
        def on_press(key):
            """Handle key press events."""
            try:
                # Add key to current set
                current_keys.add(key)
                
                # Check for Ctrl+Cmd combinations
                if (keyboard.Key.ctrl in current_keys and 
                    keyboard.Key.cmd in current_keys):
                    
                    if not hasattr(key, 'char'):
                        return
                    
                    # Map number keys to operations
                    operations = {
                        '0': ('magic', '🪄 MAGIC'),  # NEW: Context-aware magic action
                        '1': ('correct', '🔥 CORRECTION'),
                        '2': ('shorten', '✂️ SHORTEN'),
                        '3': ('rephrase', '🔄 REPHRASE'),
                        '4': ('formal', '👔 FORMAL'),
                        '5': ('respectful', '🤝 RESPECTFUL'),
                        '6': ('positive', '😊 POSITIVE')
                    }
                    
                    if key.char in operations:
                        operation, emoji_name = operations[key.char]
                        logger.info(f"{emoji_name} HOTKEY PRESSED! (Ctrl+Cmd+{key.char})")
                        if not self.is_processing:
                            logger.info(f"Processing {operation} hotkey event...")
                            # Run in separate thread to not block keyboard listener
                            threading.Thread(target=lambda op=operation: self.handle_hotkey(op), daemon=True).start()
                        else:
                            logger.warning("Already processing, ignoring hotkey press (debounce protection)")
                            # Play a subtle beep to let user know it was ignored
                            self.show_notification("Busy", "Please wait, processing previous request...")
                            
            except AttributeError:
                pass
        
        def on_release(key):
            """Handle key release events."""
            try:
                current_keys.discard(key)
            except:
                pass
        
        logger.info("Hotkey combinations registered: Ctrl+Cmd+0-6")
        
        # Start the listener
        logger.info("Starting keyboard event listener...")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
            logger.info("✓ Keyboard listener is active and monitoring")
            keyboard_listener.join()
    
    def handle_hotkey(self, operation="correct"):
        """Handle the hotkey press event.
        
        Args:
            operation: Operation to perform (correct, shorten, rephrase, formal, respectful, positive, magic)
        """
        self.current_operation = operation
        
        # Map operations to display names
        operation_names = {
            'magic': 'MAGIC (CONTEXT-AWARE)',
            'correct': 'CORRECTION',
            'shorten': 'SHORTENING',
            'rephrase': 'REPHRASING',
            'formal': 'FORMALIZATION',
            'respectful': 'RESPECTFUL REWRITE',
            'positive': 'POSITIVE REFRAME'
        }
        operation_name = operation_names.get(operation, operation.upper())
        
        logger.info("-" * 60)
        logger.info(f"STARTING TEXT {operation_name} WORKFLOW")
        logger.info("-" * 60)
        self.is_processing = True
        
        try:
            # Step 1: Simulate Cmd+C to copy selected text
            logger.info("Step 1: Simulating Cmd+C to copy selected text...")
            self.simulate_copy()
            
            # Small delay to ensure clipboard is updated
            time.sleep(0.2)
            
            # Step 2: Get text from clipboard
            logger.info("Step 2: Reading clipboard content...")
            original_text = pyperclip.paste()
            logger.info(f"Clipboard content: '{original_text[:100]}{'...' if len(original_text) > 100 else ''}'")
            
            if not original_text or not original_text.strip():
                logger.warning("No text found in clipboard")
                self.show_notification("No Text Selected", "Please select some text first.")
                return
            
            logger.info(f"Text length: {len(original_text)} characters")
            
            # Step 3: Send to Gemini for processing
            try:
                logger.info(f"Step 3: Sending text to Gemini API for {operation}...")
                
                # Call the appropriate method based on operation
                if operation == "magic":
                    # Context-aware magic processing
                    logger.info("Using context-aware magic processing...")
                    
                    # Get active window context
                    window_info = get_active_window_info()
                    if window_info:
                        app_name = window_info.get('app_name', 'Unknown')
                        persona = get_persona_for_app(app_name)
                        logger.info(f"✓ Active app: {app_name}, Persona: {persona or 'None'}")
                    else:
                        app_name = "Unknown"
                        persona = None
                        logger.warning("⚠ Could not detect context")
                    
                    # Prepare context-aware instruction
                    from gemini_client import InstructionPresets
                    base_instruction = InstructionPresets.GRAMMAR_CORRECTION
                    
                    if persona:
                        enhanced_instruction = f"You are a {persona}. {base_instruction}"
                        logger.info(f"✓ Enhanced with persona: {persona}")
                    else:
                        enhanced_instruction = base_instruction
                        logger.info("✓ Using base instruction (no persona)")
                    
                    # Process with context-aware instruction
                    processed_text = self.gemini_client.process(
                        original_text,
                        enhanced_instruction,
                        operation=f"magic ({app_name})"
                    )
                    
                elif operation == "correct":
                    processed_text = self.gemini_client.correct_text(original_text)
                elif operation == "shorten":
                    processed_text = self.gemini_client.shorten_text(original_text)
                elif operation == "rephrase":
                    processed_text = self.gemini_client.rephrase_text(original_text)
                elif operation == "formal":
                    processed_text = self.gemini_client.formalize_text(original_text)
                elif operation == "respectful":
                    processed_text = self.gemini_client.respectful_text(original_text)
                elif operation == "positive":
                    processed_text = self.gemini_client.positive_text(original_text)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                logger.info(f"✓ Received processed text from Gemini ({len(processed_text)} chars)")
                logger.info(f"Processed text: '{processed_text[:100]}{'...' if len(processed_text) > 100 else ''}'")
                
                # Step 4: Put processed text in clipboard
                logger.info("Step 4: Copying processed text to clipboard...")
                pyperclip.copy(processed_text)
                logger.info("✓ Clipboard updated with processed text")
                
                # Small delay before pasting
                time.sleep(0.1)
                
                # Step 5: Simulate Cmd+V to paste processed text
                logger.info("Step 5: Simulating Cmd+V to paste processed text...")
                self.simulate_paste()
                logger.info("✓ Paste command sent")
                
                logger.info("=" * 60)
                logger.info(f"SUCCESS! Text {operation_name.lower()} complete")
                logger.info("=" * 60)
                
                self.show_notification("Success", f"Text {operation} complete!")
                
            except ValueError as e:
                logger.error(f"Configuration error: {e}")
                self.show_notification("Configuration Error", str(e))
            except Exception as e:
                logger.error(f"Error during {operation}: {e}", exc_info=True)
                self.show_notification("Error", f"Failed to {operation} text: {str(e)}")
                # Restore original text to clipboard
                pyperclip.copy(original_text)
                logger.info("Original text restored to clipboard")
        
        finally:
            self.is_processing = False
            self.current_operation = None
            logger.info("Workflow complete. Ready for next hotkey press.")
            logger.info("")
    
    def simulate_copy(self):
        """Simulate Cmd+C keypress to copy selected text."""
        from Quartz import (
            CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap,
            CGEventSetFlags, kCGEventFlagMaskCommand
        )
        
        # Key code for 'C' is 8
        key_code_c = 8
        
        # Create Cmd+C event with Command flag
        event_down = CGEventCreateKeyboardEvent(None, key_code_c, True)
        CGEventSetFlags(event_down, kCGEventFlagMaskCommand)
        CGEventPost(kCGHIDEventTap, event_down)
        
        event_up = CGEventCreateKeyboardEvent(None, key_code_c, False)
        CGEventPost(kCGHIDEventTap, event_up)
    
    def simulate_paste(self):
        """Simulate Cmd+V keypress to paste text from clipboard."""
        from Quartz import (
            CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap,
            CGEventSetFlags, kCGEventFlagMaskCommand
        )
        
        # Key code for 'V' is 9
        key_code_v = 9
        
        # Create Cmd+V event with Command flag
        event_down = CGEventCreateKeyboardEvent(None, key_code_v, True)
        CGEventSetFlags(event_down, kCGEventFlagMaskCommand)
        CGEventPost(kCGHIDEventTap, event_down)
        
        event_up = CGEventCreateKeyboardEvent(None, key_code_v, False)
        CGEventPost(kCGHIDEventTap, event_up)
    
    def show_notification(self, title, message):
        """Show a notification to the user."""
        rumps.notification(
            title=title,
            subtitle="",
            message=message,
            sound=False
        )
    
    @rumps.clicked("Set Gemini API Key")
    def set_api_key(self, _):
        """Open dialog to set the Gemini API key."""
        # Create alert dialog
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Set Gemini API Key")
        alert.setInformativeText_("Enter your Google Gemini API key:")
        alert.addButtonWithTitle_("Save")
        alert.addButtonWithTitle_("Cancel")
        
        # Create text field
        input_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 24))
        
        # Pre-fill with existing key if available
        current_key = os.getenv('GEMINI_API_KEY', '')
        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else current_key
            input_field.setPlaceholderString_(f"Current: {masked_key}")
        else:
            input_field.setPlaceholderString_("sk-...")
        
        alert.setAccessoryView_(input_field)
        
        # Show dialog and get response
        response = alert.runModal()
        
        if response == NSAlertFirstButtonReturn:
            api_key = input_field.stringValue()
            
            if api_key:
                # Save to .env file
                env_file = find_dotenv()
                if not env_file:
                    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                    Path(env_file).touch()
                
                set_key(env_file, 'GEMINI_API_KEY', api_key)
                
                # Update client
                self.gemini_client.update_api_key(api_key)
                
                # Update environment variable
                os.environ['GEMINI_API_KEY'] = api_key
                
                # Refresh menu
                self.setup_menu()
                
                self.show_notification("Success", "API key saved successfully!")
            else:
                self.show_notification("Error", "API key cannot be empty.")
    
    @rumps.clicked("Test Connection")
    def test_connection(self, _):
        """Test the Gemini API connection."""
        logger.info("=" * 60)
        logger.info("TESTING API CONNECTION")
        logger.info("=" * 60)
        
        if not self.gemini_client.is_configured():
            logger.error("API key is not configured")
            self.show_notification("Not Configured", "Please set your API key first.")
            return
        
        logger.info("API key is configured, testing with sample text...")
        try:
            test_text = "This are a test."
            logger.info(f"Sending test text: '{test_text}'")
            result = self.gemini_client.correct_text(test_text)
            logger.info(f"✓ API response received: '{result}'")
            logger.info("=" * 60)
            logger.info("API TEST SUCCESSFUL!")
            logger.info("=" * 60)
            self.show_notification("Success", f"API connection successful! Result: {result}")
        except Exception as e:
            logger.error(f"API test failed: {e}", exc_info=True)
            logger.info("=" * 60)
            logger.error("API TEST FAILED")
            logger.info("=" * 60)
            self.show_notification("Error", f"API test failed: {str(e)}")
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """Open the log file in Console or TextEdit."""
        import subprocess
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'altgrammarly.log')
        
        if os.path.exists(log_file):
            # Open in default text editor
            subprocess.run(['open', '-a', 'Console', log_file], check=False)
            logger.info("Opened log file in Console app")
        else:
            self.show_notification("No Logs", "Log file doesn't exist yet. Try using the app first!")
            logger.warning("Log file does not exist")
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application."""
        rumps.quit_application()


def main():
    """Entry point for the application."""
    # Check if running on macOS
    if sys.platform != 'darwin':
        print("This application only runs on macOS.")
        sys.exit(1)
    
    # Start the app
    app = AltGrammarlyApp()
    app.run()


if __name__ == '__main__':
    main()
