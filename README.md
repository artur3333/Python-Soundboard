# Python-Soundboard

**Python-Soundboard** is a desktop application that allows users to play audio files through their microphone using keyboard shortcuts. The app is similar to SoundPad (same function). For now supports `.wav`, `.mp3`, and `.m4a` audio formats.

## Features

- **Audio Playback**: Play sound files through your microphone.
- **Keyboard Shortcuts**: Assign hotkeys to quickly play specific sounds.
- **Drag and Drop**: Easily add sound files to the soundboard by dragging them into the app.
- **Volume Control**: Adjust playback volume directly within the app.
- **System Tray Integration**: Minimize the application to the system tray.

## Requirements
- **Python**: 3.x
- **VB-Audio Virtual Cable** (must be installed for audio routing) Download from: [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
- **Dependencies**: Install via `requirements.txt`

## Installation

1. **Clone the repository** and navigate to the project folder:
    ```bash
    git clone https://github.com/artur3333/Python-Soundboard.git
    cd Python-Soundboard
    ```
    
2. **Install the required Python packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up VB-Audio Virtual Cable**:
   - Download and install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/).
   - Go to the `Control Panel Sound settings`:
     1. `Recording` tab.
     2. `Double tap` on your "physical" microphone.
     3. `Listen` tab.
     4. Enable `Listen to this device`.
     5. From the dropdown menu select: `"CABLE Input (VB-Audio Virtual Cable)"`.
     6. `Apply` changes and `exit`.

## Directory Tree

```plaintext
Python-Soundboard
├── sound/                  # Directory for all sound files (Will create automaticly when User run the Program)
├── main.py                 # Main script to run the application
├── config.json             # Configuration file stores: hotkeys, sounds and playscore
├── icon.ico                # Icon
├── requirements.txt        # List of Python dependencies
└── README.md               # Project readme with usage instructions and details
```

## Usage

Run the Application:
   ```bash
   python main.py
   ```
---

1. **Add Sounds**:
   - Drag and drop audio files (`.wav`, `.mp3`, `.m4a`) into the application window.

2. **Assign Shortcuts**:
   - Right-click on a sound and select "Assign Shortcut".
   - Press the desired key to assign it to the sound.

3. **Play Sounds**:
   - Press the assigned shortcut key or double-click on a sound in the list.

4. **Minimize to Tray**:
   - Close the window to minimize the application to the system tray. Access it via the tray icon.

5. **Volume Control**:
   - Use the slider in the app to adjust playback volume.

