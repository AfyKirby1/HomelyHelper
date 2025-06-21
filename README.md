# 🏠 Homely Helper

A modern Windows desktop app for planning furniture layouts with professional UI theming, door/window placement, and enhanced stability.

---
## ✨ Current Features (v0.4.3)
- **Professional Menu System** – File, View, Settings, Help menus with shortcuts
- **Theme System** – Light, Dark, and Mixed color schemes
- **Scalable Interface** – Font size adjustment for large monitors
- **Multi-unit Support** – Input sizes in metres, feet, or inches with smart conversion
- **Enhanced Zoom** – Mouse wheel zoom (Ctrl+Wheel) + improved floating 🔍+/🔍− buttons
- **Door & Window System** – Add custom-sized doors with realistic opening arcs and windows
- **Grid Snap System** – Enable grid snapping for perfect furniture alignment
- **Visual Grid Lines** – Optional grid overlay to see snap points
- **Floor Textures** – Choose from Hardwood, Carpet, Tile, Concrete backgrounds
- **Delete System** – Click X buttons or press Delete key to remove furniture
- **Room Border Toggle** – Show/hide room boundaries for precise edge placement
- **Copy/Paste/Duplicate** – Full clipboard support with right-click context menus
- **Save/Load Layouts** – Preserve your room designs in JSON format (now includes doors/windows!)
- **Drag & Drop** – Move furniture, doors, and windows around with your mouse
- **Visual Polish** – Rounded corners, hover effects, better spacing
- **Settings Persistence** – Your preferences are saved between sessions
- **Improved Stability** – Fixed canvas context menu bugs and furniture ghosting issues

---
## 🚪 Door & Window Features
- **Custom Sizing** – Set exact dimensions for doors and windows through dialog boxes
- **Smart Naming** – Auto-incremented names (Door 1, Door 2, Window 1, etc.)
- **Door Opening Animation** – Double-click doors to see realistic opening arcs
- **Rotation Support** – Right-click doors/windows and select "Rotate 90°" to change orientation
- **Full Persistence** – Doors and windows now save/load properly with room layouts
- **Visual Distinction** – Doors are white, windows are light blue
- **List Integration** – All doors and windows appear in the furniture list
- **Full Interaction** – Move, rotate, and delete doors/windows like furniture

---
## 📐 Grid Snap System (NEW!)
- **Enable Grid Snap** – Check the "Enable grid snap" option to snap furniture to a 50cm grid
- **Show Grid Lines** – Toggle "Show grid lines" to visualize the snap grid
- **Perfect Alignment** – Automatically aligns furniture for professional-looking layouts
- **Works with Everything** – Grid snap applies to furniture, doors, and windows
- **Invisible by Default** – Grid lines are optional - snap works even when lines are hidden

---
## 🖥️ One-time setup (Windows 10/11)
```powershell
# 1. Install Python 3.11 from https://python.org (✔ Add to PATH)
# 2. Grab the code (ZIP or Git clone), then inside the folder:
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---
## 🚀 Run it
```powershell
python main.py
```

---
## 📦 Build Portable Desktop App
Want to create a standalone executable that users can run without Python? Here's how:

### **Quick Build**
```powershell
# Install build tool (if not already installed)
pip install pyinstaller

# Create portable .exe file
python -m PyInstaller --onefile --windowed --name "HomelyHelper" main.py

# Your app will be in: dist\HomelyHelper.exe
```

### **Easy Build Script**
For convenience, just double-click `build_app.bat` or run:
```powershell
.\build_app.bat
```

### **What You Get**
- ✅ **Single file**: `HomelyHelper.exe` (~35MB)
- ✅ **No dependencies**: Runs on any Windows 10/11 PC
- ✅ **No installation**: Users just double-click to run
- ✅ **Portable**: Can be run from USB drives, shared folders, etc.
- ✅ **Professional**: Looks like a real desktop application

### **Distribution Tips**
- The `.exe` file is completely self-contained
- Users don't need Python, PyQt6, or any other dependencies
- Works on Windows 10/11 without any setup
- Perfect for sharing with non-technical users
- Can be distributed via email, cloud storage, or USB drives

**Quick Start:**
1. Use the left panel to set your room dimensions and click "Apply Room Size"
2. Choose a floor texture (Hardwood, Carpet, etc.) for visual appeal
3. Add furniture by filling in the name, size, and color, then "Add to Room"
4. Add doors and windows using the "Add Door" and "Add Window" buttons
5. Drag items around the canvas to position them
6. Double-click doors to see them open/close with visual arcs
7. Use **Ctrl+Wheel** or the floating 🔍+/🔍− buttons to zoom
8. Press **Delete** key or click the X button to remove items
9. Try **Settings > Preferences** to switch themes and adjust scaling
10. Save your layout with **Ctrl+S** and load it later with **Ctrl+O**

---
## 🎨 Themes & Customization
- **Light Theme** – Clean, bright interface perfect for daytime use
- **Dark Theme** – Easy on the eyes for extended sessions
- **Mixed Theme** – Best of both worlds with accent colors
- **Font Scaling** – 8pt to 24pt for any monitor size
- **Zoom Controls** – Scale the canvas view independently

---
## ⌨️ Keyboard Shortcuts
- `Ctrl+N` – New room (clears everything)
- `Ctrl+S` – Save layout to file
- `Ctrl+O` – Load layout from file
- `Ctrl+C` – Copy selected furniture
- `Ctrl+V` – Paste furniture
- `Ctrl+D` – Duplicate selected furniture
- `Ctrl+Q` – Quit application
- `Ctrl++` – Zoom in
- `Ctrl+-` – Zoom out
- `Ctrl+B` – Toggle room border
- `R` – Rotate selected furniture
- `Delete` – Delete selected items

---
## 🐛 Recent Bug Fixes (v0.4.3)
- ✅ **Door/Window Persistence** – Fixed doors and windows not saving/loading in JSON files
- ✅ **Door Rotation** – Added rotation support for doors and windows with proper opening arc updates
- ✅ **Position Tracking** – Improved door/window position tracking and persistence
- ✅ **Grid Snap System** – Added professional grid snapping for perfect furniture alignment
- ✅ **Visual Grid** – Optional grid line overlay to visualize snap points

## 🐛 Previous Bug Fixes (v0.4.2)
- ✅ **Button Reappearance** – Fixed issue where X and rotate buttons wouldn't show when reselecting furniture
- ✅ **Selection State Handling** – Improved logic for showing/hiding buttons based on selection changes
- ✅ **Button Cleanup** – Fixed hanging X and refresh buttons that stayed visible after moving furniture
- ✅ **Improved Button Management** – Better cleanup of control buttons when furniture is moved or deleted
- ✅ **Memory Management** – Enhanced widget cleanup to prevent button artifacts
- ✅ **Removed Canvas Context Menu** – Fixed buggy right-click behavior on canvas
- ✅ **Enhanced Zoom Buttons** – Clearer 🔍+/🔍− symbols instead of basic +/-
- ✅ **Door Opening Visualization** – Realistic quarter-circle arcs show door swing
- ✅ **Furniture Ghosting** – Fixed issue where furniture items left behind artifacts
- ✅ **Door/Window Sizing** – Custom dimension dialogs with proper validation
- ✅ **List Management** – Doors and windows properly appear in and remove from furniture list
- ✅ **Crash Prevention** – Better error handling and memory management

---
## 📅 Roadmap
- [x] Save/Load room layouts (JSON format) ✅
- [x] Door and window placement ✅
- [x] Copy/paste/duplicate functionality ✅
- [x] Grid overlay and snapping system ✅
- [ ] Furniture templates and presets
- [ ] Measurement tools and rulers
- [ ] 3D preview mode
- [ ] Export to image/PDF
- [ ] Wall thickness and multiple rooms

---
## 🤝 Contributing
Pull requests, feature ideas, and bug reports are welcome. This is a learning-oriented project – keep the tone friendly and constructive.

---
## 📄 Licence
MIT 