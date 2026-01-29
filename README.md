# AltGrammarly

A powerful macOS menu bar application that provides AI-powered grammar correction, text shortening, and style improvements using Google's Gemini API.

## ✨ Features

### 6 Text Operations
1. **Correct** - Fix grammar and improve clarity
2. **Shorten** - Make text concise while maintaining meaning
3. **Rephrase** - Rewrite for better flow and clarity
4. **Formalize** - Convert to professional business tone
5. **Respectful** - Make language more diplomatic and considerate
6. **Positive** - Reframe negative feedback constructively

### Multiple Access Methods
- **⌨️ Global Hotkeys** - Ctrl+Cmd+1 through 6 for instant access
- **🖱️ Right-Click Menu** - Context menu integration via Services
- **📋 Menu Bar** - Always-accessible settings and controls

## 🚀 Quick Start

### Prerequisites

- macOS 10.14 or later
- Python 3.8+
- Google Gemini API key ([Get one free here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/varunmitra/altgrammarly.git
   cd altgrammarly
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key:
   # GEMINI_API_KEY=your_api_key_here
   ```

5. **Create the macOS app** (for menu bar and hotkeys)
   - Open **Automator**
   - Create **New Application**
   - Add **Run Shell Script** action
   - Set shell to `/bin/bash`
   - Paste:
     ```bash
     cd /path/to/altgrammarly
     source venv/bin/activate
     python main.py
     ```
   - Save as `AltGrammarly.app` in Applications folder

6. **Grant Accessibility permissions**
   - System Settings → Privacy & Security → Accessibility
   - Add Terminal or AltGrammarly.app
   - Enable the checkbox ✓

7. **Launch the app**
   - Open `AltGrammarly.app` from Applications
   - Look for "AltGrammarly" in your menu bar

## 🎯 Usage

### Hotkeys (Fast & Easy)

Press the hotkey while text is selected to instantly process it:

| Hotkey | Operation | Description |
|--------|-----------|-------------|
| ⌃⌘1 | Correct | Fix grammar and improve clarity |
| ⌃⌘2 | Shorten | Make text concise |
| ⌃⌘3 | Rephrase | Rewrite for better flow |
| ⌃⌘4 | Formalize | Convert to professional tone |
| ⌃⌘5 | Respectful | Make more diplomatic |
| ⌃⌘6 | Positive | Reframe constructively |

### Right-Click Services (Optional)

1. Open **Automator** → New **Quick Action**
2. Set: "Workflow receives **text** in **any application**"
3. Check: "**Output replaces selected text**"
4. Add **Run Shell Script** action
5. Paste:
   ```bash
   cd /path/to/altgrammarly
   source venv/bin/activate
   python service_runner.py correct  # or shorten, rephrase, etc.
   ```
6. Save (e.g., "Correct Grammar with AltGrammarly")
7. Use: Select text → Right-click → Services → Your service

Repeat for other operations: `shorten`, `rephrase`, `formal`, `respectful`, `positive`

### Menu Bar

Click the AltGrammarly icon for:
- View/change API key
- Test API connection
- View debug logs
- See available hotkeys
- Quit application

## 🔧 Configuration

### API Key

Your Gemini API key is stored in `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

You can also set/update it from the menu bar: **AltGrammarly → Set Gemini API Key**

### Hotkey Customization

To change hotkeys, edit `main.py` in the `start_hotkey_listener` function. Current mappings are Ctrl+Cmd+1 through 6.

### System Instructions

To customize how Gemini processes text, edit the `SYSTEM_INSTRUCTION_*` constants in `gemini_client.py`.

## 📁 Project Structure

```
altgrammarly/
├── main.py              # Menu bar app & hotkey handler
├── gemini_client.py     # Gemini API wrapper
├── service_runner.py    # Standalone service handler
├── requirements.txt     # Python dependencies
├── .env                 # API key (not in git)
├── .env.example         # API key template
└── README.md           # This file
```

## 🐛 Troubleshooting

**Hotkeys not working?**
- Ensure Accessibility permissions are granted
- Check that AltGrammarly.app is running (icon in menu bar)
- Restart the app after granting permissions

**Services not working?**
- Verify "Output replaces selected text" is checked in Automator
- Ensure correct path to altgrammarly directory
- Check `service.log` for errors

**API errors?**
- Verify your API key is correct
- Check internet connection
- Test connection from menu bar
- View logs: AltGrammarly → View Logs

**App won't start?**
- Activate virtual environment: `source venv/bin/activate`
- Check dependencies: `pip install -r requirements.txt`
- Verify Python 3.8+: `python3 --version`

## 📋 Logs

Debug logs are written to:
- **Main app**: `altgrammarly.log`
- **Services**: `service.log`

View logs from menu bar: **AltGrammarly → View Logs**

## 🔒 Privacy & Security

- Your API key is stored locally in `.env` (never committed to git)
- Text is sent to Google's Gemini API for processing
- No data is stored or logged beyond local debug logs
- The app runs entirely on your machine

## 🚀 Advanced Usage

### Run at Login

Add `AltGrammarly.app` to **System Settings → General → Login Items**

### Custom Operations

Add new operations by:
1. Adding a `SYSTEM_INSTRUCTION_*` in `gemini_client.py`
2. Adding a method (e.g., `custom_text()`)
3. Adding hotkey mapping in `main.py`
4. Creating a service in Automator

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🙏 Acknowledgments

Built with:
- [rumps](https://github.com/jaredks/rumps) - macOS menu bar apps
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkey detection
- [Google Generative AI](https://ai.google.dev/) - Gemini API
- [pyperclip](https://github.com/asweigart/pyperclip) - Clipboard operations

## 💡 Tips

- **Select before hotkey**: Always select text before pressing hotkeys
- **Test connection**: Use menu bar to verify API is working
- **Start small**: Test with short text first
- **Multiple operations**: Try different operations on the same text to find the best result
- **Undo**: Use Cmd+Z if you don't like the result

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/varunmitra/altgrammarly/issues)
- **Discussions**: [GitHub Discussions](https://github.com/varunmitra/altgrammarly/discussions)

---

Made with ❤️ for better writing
