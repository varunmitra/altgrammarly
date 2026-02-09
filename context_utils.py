"""
Context utilities for detecting active window and app information.
Uses macOS AppKit and Quartz for clean Python integration.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from AppKit import NSWorkspace
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    APPKIT_AVAILABLE = True
except ImportError:
    logger.warning("AppKit/Quartz not available. Context detection disabled.")
    APPKIT_AVAILABLE = False


# Persona mappings: app name -> system instruction modifier
PERSONA_MAPPINGS = {
    # Development & Engineering
    'Cursor': 'Senior Software Engineer',
    'Visual Studio Code': 'Senior Software Engineer',
    'PyCharm': 'Senior Software Engineer',
    'Xcode': 'Senior Software Engineer',
    'Terminal': 'DevOps Engineer',
    'iTerm': 'DevOps Engineer',
    
    # Communication
    'Slack': 'Communication Expert',
    'Microsoft Teams': 'Communication Expert',
    'Discord': 'Communication Expert',
    'Messages': 'Communication Expert',
    'Mail': 'Professional Email Writer',
    'Outlook': 'Professional Email Writer',
    
    # Documentation & Writing
    'Notion': 'Technical Writer',
    'Obsidian': 'Technical Writer',
    'Bear': 'Technical Writer',
    'Notes': 'Note Taker',
    'Pages': 'Document Editor',
    'Microsoft Word': 'Document Editor',
    'Google Docs': 'Document Editor',
    
    # Research & Browsing
    'Safari': 'Research Analyst',
    'Google Chrome': 'Research Analyst',
    'Firefox': 'Research Analyst',
    'Arc': 'Research Analyst',
    
    # Design & Creative
    'Figma': 'UX/UI Designer',
    'Sketch': 'UX/UI Designer',
    'Adobe Photoshop': 'Creative Professional',
    
    # Productivity
    'Jira': 'Project Manager',
    'Linear': 'Project Manager',
    'Asana': 'Project Manager',
    'Trello': 'Project Manager',
}


def get_active_window_info() -> Optional[Dict[str, str]]:
    """
    Get information about the currently focused window.
    
    Returns:
        Dictionary with 'app_name' and 'window_title' keys, or None if unavailable.
        
    Example:
        {
            'app_name': 'Cursor',
            'window_title': 'main.py - altgrammarly'
        }
    """
    if not APPKIT_AVAILABLE:
        logger.warning("AppKit not available - cannot detect active window")
        return None
    
    try:
        # Get the active application using NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()
        
        if not active_app:
            logger.warning("No active application found")
            return None
        
        app_name = active_app.get('NSApplicationName', 'Unknown')
        
        # Get the frontmost window title using Quartz
        window_title = _get_frontmost_window_title()
        
        result = {
            'app_name': app_name,
            'window_title': window_title or ''
        }
        
        logger.debug(f"Active window: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get active window info: {e}", exc_info=True)
        return None


def _get_frontmost_window_title() -> Optional[str]:
    """
    Get the title of the frontmost window using Quartz.
    
    Returns:
        Window title string, or None if not available.
    """
    try:
        # Get list of all on-screen windows
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )
        
        # The first window in the list is typically the frontmost one
        if window_list and len(window_list) > 0:
            for window in window_list:
                # Look for windows with layer 0 (normal windows)
                if window.get('kCGWindowLayer', -1) == 0:
                    title = window.get('kCGWindowName', '')
                    if title:
                        return title
        
        return None
        
    except Exception as e:
        logger.debug(f"Failed to get window title: {e}")
        return None


def get_persona_for_app(app_name: str) -> Optional[str]:
    """
    Map an application name to a persona/role.
    
    Args:
        app_name: Name of the application (e.g., 'Slack', 'Cursor')
        
    Returns:
        Persona string (e.g., 'Communication Expert'), or None if no mapping exists.
        
    Example:
        >>> get_persona_for_app('Slack')
        'Communication Expert'
        >>> get_persona_for_app('Cursor')
        'Senior Software Engineer'
    """
    return PERSONA_MAPPINGS.get(app_name)


def get_context_aware_instruction(base_instruction: str) -> str:
    """
    Enhance a base system instruction with context from the active window.
    
    Args:
        base_instruction: The base system instruction to enhance.
        
    Returns:
        Enhanced instruction with persona context, or original if context unavailable.
        
    Example:
        If user is in Slack:
        Input:  "Correct the grammar..."
        Output: "You are a Communication Expert. Correct the grammar..."
    """
    window_info = get_active_window_info()
    
    if not window_info:
        return base_instruction
    
    app_name = window_info.get('app_name', '')
    persona = get_persona_for_app(app_name)
    
    if persona:
        # Prepend persona context to the instruction
        enhanced = f"You are a {persona}. {base_instruction}"
        logger.info(f"Enhanced instruction with persona: {persona} (from {app_name})")
        return enhanced
    else:
        logger.debug(f"No persona mapping for app: {app_name}")
        return base_instruction


def get_all_personas() -> Dict[str, str]:
    """
    Get all available persona mappings.
    
    Returns:
        Dictionary of app_name -> persona mappings.
    """
    return PERSONA_MAPPINGS.copy()


def add_persona_mapping(app_name: str, persona: str) -> None:
    """
    Add or update a persona mapping for an application.
    
    Args:
        app_name: Name of the application.
        persona: Persona/role description.
        
    Example:
        >>> add_persona_mapping('IntelliJ IDEA', 'Senior Java Developer')
    """
    PERSONA_MAPPINGS[app_name] = persona
    logger.info(f"Added persona mapping: {app_name} -> {persona}")


# Example usage and testing
if __name__ == '__main__':
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Context Utils Testing")
    print("=" * 60)
    print()
    
    # Test 1: Get active window info
    print("Test 1: Get Active Window Info")
    print("-" * 60)
    window_info = get_active_window_info()
    if window_info:
        print(f"✓ App Name:      {window_info['app_name']}")
        print(f"✓ Window Title:  {window_info['window_title']}")
    else:
        print("✗ Could not detect active window")
    print()
    
    # Test 2: Get persona for current app
    if window_info:
        print("Test 2: Get Persona for Active App")
        print("-" * 60)
        persona = get_persona_for_app(window_info['app_name'])
        if persona:
            print(f"✓ Persona: {persona}")
        else:
            print(f"⚠ No persona mapped for: {window_info['app_name']}")
        print()
    
    # Test 3: Context-aware instruction
    print("Test 3: Context-Aware Instruction Enhancement")
    print("-" * 60)
    base = "Correct the grammar and improve clarity."
    enhanced = get_context_aware_instruction(base)
    print(f"Base:     {base}")
    print(f"Enhanced: {enhanced}")
    print()
    
    # Test 4: Show all personas
    print("Test 4: All Available Personas")
    print("-" * 60)
    all_personas = get_all_personas()
    for app, persona in sorted(all_personas.items()):
        print(f"  {app:30s} → {persona}")
    print()
    
    print("=" * 60)
    print(f"Total personas mapped: {len(all_personas)}")
    print("=" * 60)
