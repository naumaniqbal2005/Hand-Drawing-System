# Hand Drawing System

A real-time hand tracking application that allows you to draw, erase, and change colors using hand gestures powered by MediaPipe and computer vision.

## 🎨 Features

- **👆 Real-time Hand Tracking**: Uses MediaPipe for accurate hand detection
- **✏️ Gesture-based Drawing**: Draw with 1 finger
- **🌈 Color Changing**: Switch between white, green, and vibrant blue with 2-4 fingers
- **🧹 Smart Eraser**: Erase with 5 fingers
- **⚡ Instant Response**: Zero-delay gesture recognition
- **🌙 Dark Theme**: Modern dark UI interface
- **📹 Live Camera Feed**: Real-time video streaming with hand overlay
- **🎯 Responsive Design**: Clean and smooth user interface

## 🚀 Quick Start

### Prerequisites

- Python 3.9-3.11
- Node.js 14+
- Webcam camera

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/naumaniqbal2005/Hand-Drawing-System.git
cd Hand-Drawing-System/backend

# Install Python dependencies
py -3.9 -m pip install -r requirements.txt

# Start the backend server
py -3.9 server.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install Node.js dependencies
npm install

# Start the React development server
npm start
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/api/hand-data
- **Video Feed**: http://localhost:5000/video_feed

## 🎮 How to Use

### Hand Gestures

| Fingers | Action | Color |
|---------|--------|-------|
| 1 Finger | ✏️ Draw | Current Color |
| 2 Fingers | ⚪ White Color | White |
| 3 Fingers | 🟢 Green Color | Green |
| 4 Fingers | 🔵 Vibrant Blue | Vibrant Blue |
| 5 Fingers | 🧹 Eraser | - |
| 0 Fingers | ⏸️ Idle | - |

### Controls

- **Start Camera**: Begin hand tracking and drawing
- **Stop Camera**: Pause camera feed
- **Clear Canvas**: Reset the drawing canvas

## 🏗️ Project Structure

```
Hand-Drawing-System/
├── backend/
│   ├── server.py          # Flask server with hand tracking
│   ├── requirements.txt    # Python dependencies
│   └── hand_landmarker.task # MediaPipe model
├── frontend/
│   ├── package.json       # React dependencies
│   ├── public/
│   │   └── index.html      # HTML template
│   └── src/
│       ├── App.jsx        # Main React component
│       ├── App.css        # Styling
│       ├── index.js       # React entry point
│       └── index.css      # Base styles
└── main.py                # Original standalone version
```

## 🛠️ Technologies Used

### Backend
- **Flask**: Web framework for API server
- **MediaPipe**: Hand detection and tracking
- **OpenCV**: Computer vision and image processing
- **NumPy**: Numerical computing

### Frontend
- **React**: Modern UI framework
- **CSS3**: Dark theme styling
- **Axios**: HTTP requests (via fetch)

## 🎯 Key Features Explained

### Hand Tracking Algorithm
- **Orientation Awareness**: Detects palm facing direction
- **Stable Finger Counting**: Reduces jitter with delay mechanism
- **Real-time Processing**: Instant gesture recognition (0-frame delay)
- **Multi-hand Support**: Can track up to 2 hands simultaneously

### Drawing System
- **Smooth Lines**: Connects finger positions for continuous drawing
- **Canvas Overlay**: Persistent drawing layer on video feed
- **Color Management**: Real-time color switching
- **Eraser Tool**: Large circular eraser with 70px radius

### Performance Optimizations
- **Error Handling**: Robust camera reconnection logic
- **CORS Enabled**: Cross-origin request support
- **Memory Efficient**: Optimized canvas operations
- **Responsive UI**: Smooth animations and transitions

## 🔧 Configuration

### Environment Variables
```bash
# Backend (optional)
FLASK_ENV=development
FLASK_DEBUG=False

# Frontend (optional)
REACT_APP_API_URL=http://localhost:5000
```

### Customization
- **Eraser Size**: Modify `eraser_size` in `server.py`
- **Colors**: Update color tuples in `process_hand_landmarks()`
- **Delay**: Adjust `stable_count_frames` for responsiveness vs stability
- **Camera**: Change camera index in `cv2.VideoCapture(0)`

## 🐛 Troubleshooting

### Common Issues

**Camera not working:**
```bash
# Try different camera indices
camera = cv2.VideoCapture(1)  # or 2, 3, etc.
```

**MediaPipe not found:**
```bash
# Ensure hand_landmarker.task is in backend folder
# Reinstall MediaPipe
py -3.9 -m pip install mediapipe
```

**CORS errors:**
- Ensure backend is running before frontend
- Check CORS configuration in `server.py`

**Hand tracking not detected:**
- Ensure good lighting
- Check camera permissions
- Verify MediaPipe model file exists

### Performance Tips

- **Reduce resolution** for better performance
- **Adjust delay** for stability vs responsiveness
- **Use wired connection** for camera if possible

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **MediaPipe**: For hand tracking technology
- **OpenCV**: For computer vision capabilities
- **React**: For the modern frontend framework
- **Flask**: For the lightweight backend API

## 📞 Contact

Created by [Nauman Iqbal](https://github.com/naumaniqbal2005)

---

**🎨 Start drawing with your hands today!**
