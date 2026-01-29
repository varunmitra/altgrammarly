# Adding AltGrammarly to Right-Click Menu (macOS Services)

## Overview
You can add AltGrammarly operations to the right-click context menu using macOS Services/Quick Actions.

## Setup Instructions

### Service 1: Correct Grammar (Right-Click)

1. **Open Automator**
   - Press Cmd+Space, type "Automator", press Enter

2. **Create New Quick Action**
   - Click "New Document"
   - Choose "Quick Action" (or "Service" on older macOS)

3. **Configure Service Settings** (at the top)
   - "Workflow receives current" → **text**
   - "in" → **any application**
   - Check "Output replaces selected text"

4. **Add "Run Shell Script" Action**
   - Search for "Run Shell Script" in the left panel
   - Drag it to the workflow area

5. **Configure the Script**
   - "Shell:" → `/bin/bash`
   - "Pass input:" → **to stdin**
   - Paste this script:
   ```bash
   cd /Users/vmitra/Work/VibeCode/altgrammarly
   source venv/bin/activate
   python service_runner.py correct
   ```

6. **Save the Service**
   - File → Save (Cmd+S)
   - Name: "Correct Grammar with AltGrammarly"
   - Location will default to ~/Library/Services/

---

### Service 2: Shorten Text (Right-Click)

Repeat the same steps but:
- In step 5, change the script to:
  ```bash
  cd /Users/vmitra/Work/VibeCode/altgrammarly
  source venv/bin/activate
  python service_runner.py shorten
  ```
- In step 6, name it: "Shorten Text with AltGrammarly"

---

## Using the Services

1. **Select any text** in any application
2. **Right-click** on the selection
3. **Navigate to "Services" submenu** (or "Quick Actions")
4. **Choose:**
   - "Correct Grammar with AltGrammarly" or
   - "Shorten Text with AltGrammarly"
5. **The selected text will be replaced** with the processed version

---

## Keyboard Shortcuts for Services (Optional)

You can assign keyboard shortcuts to these services:

1. **Open System Settings** → **Keyboard** → **Keyboard Shortcuts**
2. Select **"Services"** from left sidebar
3. Find your AltGrammarly services under "Text"
4. Click on the service and click "Add Shortcut"
5. Press your desired key combination

**Suggested shortcuts:**
- Correct Grammar: Cmd+Shift+G (if not conflicting)
- Shorten Text: Cmd+Shift+S (if not conflicting)

---

## Troubleshooting

**Services don't appear in right-click menu:**
1. Make sure you selected "text" as input type
2. Restart the application you're testing in
3. Log out and log back in (services cache)

**Services appear but don't work:**
1. Check the paths in the shell script are correct
2. Test the service_runner.py manually:
   ```bash
   cd /Users/vmitra/Work/VibeCode/altgrammarly
   source venv/bin/activate
   echo "This are a test" | python service_runner.py correct
   ```

**Service is slow:**
- First run may be slow as Python starts up
- Subsequent runs should be faster

---

## Alternative: Right-Click Menu (Advanced)

For a true right-click integration (without Services submenu), you would need to:
1. Create a FinderSync or NSServices extension
2. Build as a proper macOS app bundle
3. Code sign the app

This is more complex and requires Xcode. The Services approach above is simpler and works well.

---

## Current Features Summary

**Hotkeys (Always Active):**
- Ctrl+Cmd+1 → Correct Grammar
- Ctrl+Cmd+2 → Shorten Text

**Right-Click (After Setup):**
- Services → Correct Grammar with AltGrammarly
- Services → Shorten Text with AltGrammarly

**Menu Bar:**
- Click icon for settings and testing
