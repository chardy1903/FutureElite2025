# FutureElite Tracker

A privacy-first, offline desktop application for tracking youth football (soccer) matches. Built specifically for Brodie Hardy of Al Qadsiah U12, this app allows you to log matches, track statistics, and generate professional PDF reports.

## 🏆 Features

- **Privacy-First**: All data stored locally, no cloud, no telemetry, no analytics
- **Offline Operation**: No internet required at runtime
- **Match Logging**: Track pre-season friendlies and league matches
- **Statistics Tracking**: Goals, assists, minutes played, wins/draws/losses
- **Professional PDF Reports**: A4 landscape reports with exact styling
- **Upcoming Fixtures**: Manage future matches
- **Data Export/Import**: Backup and restore your data
- **Cross-Platform**: Windows (.exe) and macOS (.app) support

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows 10+ or macOS 10.15+

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd GoalTracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   **Windows:**
   ```cmd
   venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

The application will open automatically in your default browser at `http://127.0.0.1:5000`.

## 📦 Building Executables

### Windows

Run the PowerShell build script:

```powershell
.\build_windows.ps1
```

This creates `dist\FutureEliteTracker.exe` - a single-file executable.

**Creating a Desktop Shortcut:**
1. Right-click on your desktop
2. Select "New" > "Shortcut"
3. Browse to `dist\FutureEliteTracker.exe`
4. Name it "FutureElite Tracker"
5. Click "Finish"

### macOS

Run the shell build script:

```bash
./build_macos.sh
```

This creates `dist\FutureEliteTracker.app` - a macOS application bundle.

**Installing the App:**
1. Drag `FutureEliteTracker.app` to your Applications folder
2. Double-click the app in Applications to run it
3. On first run, you may need to right-click and select "Open" due to macOS security

## 📊 Usage

### Dashboard

The main dashboard shows:
- Season summary statistics
- Recent matches
- Upcoming fixtures
- Quick action buttons

### Logging Matches

1. Click "Log Match" button
2. Fill in the match details:
   - **Category**: Pre-Season Friendly or League
   - **Date**: Match date
   - **Opponent**: Team name (supports emojis)
   - **Location**: Venue
   - **Result**: Win/Draw/Loss
   - **Score**: Format as "7 - 5"
   - **Brodie's Stats**: Goals, assists, minutes played
   - **Notes**: Additional details
3. Check "Upcoming fixture" for future matches without stats
4. Click "Save Match"

### Generating PDF Reports

1. Click "Generate PDF" on the dashboard
2. The app creates a professional A4 landscape PDF
3. The PDF includes:
   - Season summary table
   - Pre-season friendlies table
   - League groups and qualification info
   - Professional styling with Qadsiah colors

### Managing Data

- **Export**: Click "Export/Import" to download a ZIP backup
- **Import**: Upload a previous backup to restore data
- **Settings**: Customize club info, colors, and league groups

## 🎨 Customization

### Settings

Access settings via the navigation menu to customize:
- Season year
- Club and player names
- Primary colors (default: Qadsiah red #B22222)
- League groups and team names
- Footer text

### League Groups

The app includes pre-configured league groups for Eastern Province U12 League 2025/26:

**Group 1:** Winners Club, Dhahran Sports, Al-Qadsiah, Al-Dhanna Academy, Kat Academy, The Talented Player, Generations of Excellence, Al-Ibtisam, Al-Khaleej, Al-Ettifaq, Al-Salam

**Group 2:** Al-Huda, Al-Moheet, Al-Noor, Mudhar Club, Ashbal Al-Baraem, Al-Nojoom Al-Mudhee'na (The Shining Stars), H.S. Sport, Meridiana, Khaled Mubarak Sports, Generations Sports, Aspire

## 📁 Project Structure

```
GoalTracker/
├── app/
│   ├── __init__.py
│   ├── main.py              # Flask application
│   ├── routes.py            # API routes
│   ├── models.py            # Pydantic data models
│   ├── storage.py           # JSON file operations
│   ├── pdf.py              # PDF generation
│   ├── utils.py            # Utility functions
│   ├── templates/          # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── matches.html
│   │   └── settings.html
│   ├── static/             # Static assets
│   └── data/               # Local data storage
│       ├── matches.json
│       └── settings.json
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
├── build_windows.ps1      # Windows build script
├── build_macos.sh         # macOS build script
├── run.py                 # Main entry point
└── README.md
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or run individual test files:

```bash
python tests/test_storage.py
python tests/test_pdf.py
python tests/test_utils.py
```

## 🔒 Privacy & Security

- **No Internet Required**: App works completely offline
- **Local Storage Only**: All data stored in JSON files on your device
- **No Telemetry**: No usage tracking or analytics
- **No Cloud Sync**: Data never leaves your device
- **Open Source**: Full source code available for inspection

## 🛠️ Technical Details

### Technology Stack

- **Backend**: Python 3.11, Flask
- **Frontend**: HTML, TailwindCSS (CDN), Vanilla JavaScript
- **PDF Generation**: ReportLab
- **Data Storage**: Local JSON files
- **Packaging**: PyInstaller
- **Validation**: Pydantic

### Data Format

Matches are stored in `data/matches.json` with the following structure:

```json
{
  "id": "20251023_120000",
  "category": "Pre-Season Friendly",
  "date": "23 Oct 2025",
  "opponent": "Dhahran Academy",
  "location": "Offside Arena",
  "result": "Win",
  "score": "7 - 5",
  "brodie_goals": 1,
  "brodie_assists": 1,
  "minutes_played": 30,
  "notes": "Scored from edge of box...",
  "is_fixture": false
}
```

## 🐛 Troubleshooting

### Common Issues

**App won't start:**
- Ensure Python 3.11+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Try running: `python run.py`

**PDF generation fails:**
- Check that the `output` directory exists and is writable
- Ensure ReportLab is properly installed

**Data not saving:**
- Check that the `data` directory exists and is writable
- Verify file permissions

**Build fails:**
- Ensure PyInstaller is installed: `pip install PyInstaller`
- Check that all dependencies are in requirements.txt
- Try cleaning previous builds: delete `dist` and `build` folders

### Getting Help

1. Check the console output for error messages
2. Verify all dependencies are installed correctly
3. Ensure you're using Python 3.11 or higher
4. Check file permissions in the project directory

## 📝 Sample Data

The app comes pre-loaded with sample pre-season friendlies:

1. **11 Sep 2025** — OLE Academy — Win 3-2 (1 goal, 20 min)
2. **09 Oct 2025** — Ettifaq Club — Loss 2-3 (2 goals, 40 min)
3. **16 Oct 2025** — Al Hilal — Loss 3-5 (0 goals, 20 min)
4. **17 Oct 2025** — Al Fatah — Loss 2-3 (1 goal, 40 min)
5. **23 Oct 2025** — Dhahran Academy — Win 7-5 (1 goal, 1 assist, 30 min)
6. **28 Oct 2025** — Bahrain National Team 🇧🇭 — (upcoming fixture)
7. **30 Oct 2025** — Winners Academy ❤️💛 — (upcoming fixture)

## 🎯 Future Enhancements

Potential features for future versions:
- Match photos and videos
- Advanced statistics and analytics
- Multiple player support
- Custom report templates
- Match calendar integration
- Team management features

## 📄 License

This project is built for personal use. All data remains private and local to your device.

---

**FutureElite Tracker** - Tracking Brodie's journey to football excellence! ⚽🏆








