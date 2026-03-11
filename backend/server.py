from flask import Flask, Response, jsonify
from flask_cors import CORS
import cv2
import mediapipe as mp
import numpy as np
import time

# Create Flask server
server = Flask(__name__)
CORS(server, 
    origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True
)  # Enable CORS for frontend

# Global variables for drawing
drawing_canvas = None
drawing = False
last_pos = None
eraser_size = 70  # Size of eraser when using 5 fingers
color = (0, 255, 0)  # Default drawing color (green)
current_mode = 'idle'
finger_count = 0

# Finger counting delay variables
last_finger_count = 0
finger_count_delay = 0
stable_count_frames = 0  # Instant response - no delay

# Initialize MediaPipe
try:
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    # Create the hand landmarker
    base_options = BaseOptions(model_asset_path='hand_landmarker.task')
    options = HandLandmarkerOptions(
        base_options=base_options,
        running_mode=VisionRunningMode.IMAGE,
        num_hands=2)
    landmarker = HandLandmarker.create_from_options(options)
    print("MediaPipe hand landmarker initialized successfully")
except Exception as e:
    print(f"Error initializing MediaPipe: {e}")
    landmarker = None

def initialize_canvas(width, height):
    """Initialize the drawing canvas"""
    global drawing_canvas
    drawing_canvas = np.zeros((height, width, 3), dtype=np.uint8)
    
def overlay_canvas(image):
    """Overlay the existing canvas on the image without drawing anything new"""
    overlay = image.copy()
    mask = drawing_canvas > 0
    overlay[mask] = drawing_canvas[mask]
    return overlay

def draw_on_canvas(image, finger_pos, finger_mcp, is_eraser=False):
    """Draw or erase on the canvas"""
    global drawing_canvas, color, last_pos
    
    if is_eraser:
        # Erase area around finger position
        cv2.circle(drawing_canvas, finger_mcp, eraser_size, (0, 0, 0), -1)
        last_pos = None
        
    else:
        # Draw at finger position
        if last_pos is not None:
            # Draw line from last position to current for smooth drawing
            cv2.line(drawing_canvas, last_pos, finger_pos, color, 3)
        else:
            # Draw point if no previous position
            cv2.circle(drawing_canvas, finger_pos, 3, color, -1)
        last_pos = finger_pos
    
    # Overlay canvas on main image
    return overlay_canvas(image)

def get_finger_tip_position(landmarks, image_shape):
    """Get the pixel position of the index finger tip"""
    landmark_list = landmarks if isinstance(landmarks, list) else landmarks.landmark
    height, width, _ = image_shape
    
    # Index finger tip is landmark 8
    tip = landmark_list[8]
    x = int(tip.x * width)
    y = int(tip.y * height)
    return (x, y)

def get_finger_mcp_position(landmarks, image_shape):
    """Get the pixel position of the index finger MCP (middle phalange)"""
    landmark_list = landmarks if isinstance(landmarks, list) else landmarks.landmark
    height, width, _ = image_shape
    
    # Index finger MCP is landmark 6
    mcp = landmark_list[6]
    x = int(mcp.x * width)
    y = int(mcp.y * height)
    return (x, y)

def count_fingers_improved(landmarks):
    """Improved finger counting with orientation awareness and sensitivity buffers"""
    landmark_list = landmarks if isinstance(landmarks, list) else landmarks.landmark
    
    # Check hand orientation (palm facing camera vs away)
    wrist = landmark_list[0]
    middle_finger_mcp = landmark_list[9]
    
    # Calculate hand orientation using wrist to middle finger vector
    hand_vector_x = middle_finger_mcp.x - wrist.x
    palm_facing_camera = hand_vector_x > 0
    
    fingers_up = 0
    extension_buffer = 0.03
    
    # Thumb detection
    thumb_tip = landmark_list[4]
    thumb_mcp = landmark_list[2]
    
    if palm_facing_camera:
        thumb_extended = (thumb_tip.x > (thumb_mcp.x + 0.04) and thumb_tip.y < (thumb_mcp.y - 0.02))
    else:
        thumb_extended = (thumb_tip.x < (thumb_mcp.x - 0.04) and thumb_tip.y < (thumb_mcp.y - 0.02))
    
    if thumb_extended:
        fingers_up += 1
    
    # Other fingers
    finger_tips = [8, 12, 16, 20]
    finger_bases = [6, 10, 14, 18]
    
    for tip_idx, base_idx in zip(finger_tips, finger_bases):
        tip = landmark_list[tip_idx]
        base = landmark_list[base_idx]
        
        if tip.y < (base.y - extension_buffer):
            fingers_up += 1
    
    return fingers_up

def process_hand_landmarks(landmarks, frame_shape):
    """Process hand landmarks and update global state"""
    global current_mode, finger_count, color, last_finger_count, finger_count_delay
    global last_pos
    
    current_finger_count = count_fingers_improved(landmarks)
    
    # Only update finger count if it's different from last count
    if current_finger_count != last_finger_count:
        last_finger_count = current_finger_count
        finger_count_delay = 0
    else:
        finger_count_delay += 1
    
    # Only use finger count after delay period
    if finger_count_delay >= stable_count_frames:
        finger_count = current_finger_count
        
        # Handle drawing/erasing based on stable count
        finger_pos = get_finger_tip_position(landmarks, frame_shape)
        finger_mcp = get_finger_mcp_position(landmarks, frame_shape)
        
        if finger_count == 1:
            current_mode = 'drawing'
        elif finger_count == 5:
            current_mode = 'erasing'
        elif finger_count == 2:
            current_mode = 'color-change'
            color = (0, 255, 0)  # Green
            last_pos = None
            
        elif finger_count == 3:
            current_mode = 'color-change'
            color = (255, 255, 255)  # white
            last_pos = None
        elif finger_count == 4:
            current_mode = 'color-change'
            color = (243, 150, 33)  # True vibrant blue (BGR)
            last_pos = None
        else:
            current_mode = 'idle'
            last_pos = None
    
    # IMMEDIATELY stop drawing when fingers drop to 0
    if current_finger_count == 0:

        last_pos = None
    
    print(f"DEBUG: Fingers={current_finger_count}, Mode={current_mode}, Color={get_color_name()}")

def get_color_name():
    """Convert color tuple to color name"""
    global color
    if color == (0, 255, 0):
        return 'green'
    elif color == (255, 255, 255):
        return 'white'  # Fixed: was returning 'red' incorrectly
    elif color == (243, 150, 33):
        return 'vibrant blue'
    else:
        return 'unknown'

def draw_landmarks(image, landmarks):
    """Draw hand landmarks manually"""
    height, width, _ = image.shape
    
    try:
        landmark_list = landmarks if isinstance(landmarks, list) else landmarks.landmark
        
        for i, landmark in enumerate(landmark_list):
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            
        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
            (5, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
            (9, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
            (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (0, 17)  # Palm
        ]
        
        for start_idx, end_idx in connections:
            if start_idx < len(landmark_list) and end_idx < len(landmark_list):
                start = landmark_list[start_idx]
                end = landmark_list[end_idx]
                start_x, start_y = int(start.x * width), int(start.y * height)
                end_x, end_y = int(end.x * width), int(end.y * height)
                cv2.line(image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)
                
    except Exception as e:
        print(f"Error drawing landmarks: {e}")

# Open camera
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    camera = cv2.VideoCapture(1)  # Try camera 1

# Get camera dimensions and initialize canvas
width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
initialize_canvas(width, height)
print(f"Camera opened: {width}x{height}")

# Generator to stream frames
def generate_frames():
    global current_mode, finger_count, color
    
    while True:
        try:
            success, frame = camera.read()
            if not success:
                print("Camera read failed, attempting to reconnect...")
                # Try to reconnect camera
                camera.release()
                time.sleep(1)
                camera.open(0)
                if not camera.isOpened():
                    camera.open(1)
                continue

            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Only try hand tracking if MediaPipe was initialized successfully
            if landmarker:
                try:
                    # Convert BGR image to RGB
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Create MediaPipe image object
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                    
                    # Detect hands
                    results = landmarker.detect(mp_image)
                    
                    # Draw hand landmarks
                    if results.hand_landmarks:
                        for hand_landmarks in results.hand_landmarks:
                            draw_landmarks(frame, hand_landmarks)
                            
                            # Process hand landmarks for drawing/erasing
                            process_hand_landmarks(hand_landmarks, frame.shape)
                            
                            # Get finger positions for drawing
                            finger_pos = get_finger_tip_position(hand_landmarks, frame.shape)
                            finger_mcp = get_finger_mcp_position(hand_landmarks, frame.shape)
                            
                            # Draw/erase based on current mode
                            if finger_count == 1:
                                frame = draw_on_canvas(frame, finger_pos, finger_mcp, is_eraser=False)
                            elif finger_count == 5:
                                frame = draw_on_canvas(frame, finger_pos, finger_mcp, is_eraser=True)
                    
                except Exception as e:
                    print(f"Error during hand detection: {e}")
                    # Continue with frame even if hand detection fails

            # Overlay drawing canvas on frame
            frame = overlay_canvas(frame)

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield in the format Flask expects for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
        except Exception as e:
            print(f"Critical error in frame generation: {e}")
            # Generate a blank frame if camera fails
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Route to stream video
@server.route('/video_feed')
def video_feed():
    def generate():
        for frame in generate_frames():
            yield frame
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                    })

# Route to get hand tracking data
@server.route('/api/hand-data', methods=['GET'])
def get_hand_data():
    """API endpoint to get current hand tracking data"""
    global current_mode, finger_count, color
    
    return jsonify({
        'finger_count': finger_count,
        'current_color': get_color_name(),
        'current_mode': current_mode,
        'timestamp': time.time()
    })

# Route to clear canvas
@server.route('/clear', methods=['POST'])
def clear():
    global drawing_canvas, last_pos
    if drawing_canvas is not None:
        drawing_canvas[:] = 0
    last_pos = None
    return "canvas cleared"

# Run server
if __name__ == "__main__":
    print("Hand tracking server running on http://localhost:5000")
    print("Video feed: http://localhost:5000/video_feed")
    print("API endpoint: http://localhost:5000/api/hand-data")
    print("Starting camera and hand tracking...")
    
    try:
        server.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        print("Make sure port 5000 is not in use")
