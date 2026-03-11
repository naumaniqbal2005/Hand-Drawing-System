import cv2
import mediapipe as mp
import time
import numpy as np

# Global variables for drawing
drawing_canvas = None
drawing = False
last_pos = None
eraser_size = 70  # Size of eraser when using 5 fingers
color = (0, 255, 0)  # Default drawing color (green)


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

def draw_on_canvas(image, finger_pos,finger_mcp, is_eraser=False):
    """Draw or erase on the canvas"""
    global drawing_canvas, color
    
    if is_eraser:
        # Erase area around finger position
        cv2.circle(drawing_canvas, finger_mcp, eraser_size, (0, 0, 0), -1)
    else:
        # Draw at finger position
        global last_pos
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
    """
    Improved finger counting with orientation awareness and sensitivity buffers
    Returns: Number of fingers raised (0-5)
    """
    landmark_list = landmarks if isinstance(landmarks, list) else landmarks.landmark
    
    # Check hand orientation (palm facing camera vs away)
    wrist = landmark_list[0]
    middle_finger_mcp = landmark_list[9]
    
    # Calculate hand orientation using wrist to middle finger vector
    hand_vector_x = middle_finger_mcp.x - wrist.x
    palm_facing_camera = hand_vector_x > 0  # Positive = palm facing camera
    
    fingers_up = 0
    extension_buffer = 0.03  # Buffer for less sensitive detection
    
    # Thumb detection - check if thumb is extended outward
    # Adjust logic based on hand orientation
    thumb_tip = landmark_list[4]
    
    thumb_mcp = landmark_list[2]
    
    if palm_facing_camera:
        # Palm facing camera - thumb should point right
        # Make less sensitive: require significant horizontal extension AND upward movement
        thumb_extended = (thumb_tip.x > (thumb_mcp.x + 0.04) and thumb_tip.y < (thumb_mcp.y - 0.02))
    else:
        # Palm away from camera - thumb should point left
        # Make less sensitive: require significant horizontal extension AND upward movement
        thumb_extended = (thumb_tip.x < (thumb_mcp.x - 0.04) and thumb_tip.y < (thumb_mcp.y - 0.02))
    
    if thumb_extended:
        fingers_up += 1
    
    # Other fingers - check extension with buffer
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
    finger_bases = [6, 10, 14, 18]  # Corresponding PIP joints
    
    for i, (tip_idx, base_idx) in enumerate(zip(finger_tips, finger_bases), start=1):
        tip = landmark_list[tip_idx]
        base = landmark_list[base_idx]
        
        # Check if finger is extended with buffer
        if tip.y < (base.y - extension_buffer):
            fingers_up += 1
    
    return fingers_up

def draw_landmarks(image, landmarks):
    """Draw hand landmarks manually"""
    height, width, _ = image.shape


    
    # Draw each landmark point
    try:
        # The new API returns landmarks as a list directly
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
        # Just draw a simple circle in the center as fallback
        cv2.circle(image, (width//2, height//2), 10, (0, 0, 255), -1)




def main():
    print("The code is running..")
    global color

    try:
        # Initialize MediaPipe Hands with the new API
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
        print("Running without hand tracking...")
        landmarker = None

    # Try camera 0 first (most common), then 1
    for camera_index in [0, 1]:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            print(f"Camera opened successfully at index {camera_index}")
            break
        else:
            print(f"Cannot open camera at index {camera_index}")
            cap.release()
    else:
        print("No camera found")
        return
    
    # Get camera dimensions and initialize drawing canvas
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    initialize_canvas(width, height)
    print(f"Drawing canvas initialized: {width}x{height}")

    while True:
        success, img = cap.read()
        if not success:
            print("Unable to read feed")
            break

        img = cv2.flip(img, 1)
        
        # Always overlay the drawing canvas on the main image
        img = overlay_canvas(img)  # Just overlay, don't draw
        
        # Only try hand tracking if MediaPipe was initialized successfully
        if landmarker:
            try:
                # Convert the BGR image to RGB
                rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe image object
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Detect hands
                results = landmarker.detect(mp_image)
                
                
                # Draw hand landmarks
                if results.hand_landmarks:
                    for hand_landmarks in results.hand_landmarks:
                        draw_landmarks(img, hand_landmarks)
                        
                        # Count fingers and handle drawing/erasing
                        
                        finger_count = count_fingers_improved(hand_landmarks)
                        print(f"Fingers up: {finger_count}")
                       
                        
                        # Get finger tip position for drawing
                        finger_pos = get_finger_tip_position(hand_landmarks, img.shape)
                        finger_mcp = get_finger_mcp_position(hand_landmarks, img.shape)
                        if finger_count == 1:
                            # Draw mode - one finger up
                            img = draw_on_canvas(img, finger_pos,finger_mcp, is_eraser=False)
                            print("Drawing mode")
                        elif finger_count == 5:
                            # Eraser mode - five fingers up
                            img = draw_on_canvas(img, finger_pos,finger_mcp, is_eraser=True)
                            print("Eraser mode")
                        elif finger_count == 2:
                            # Color change mode - two fingers up
                            color = (0, 0, 255)  # Red
                            print("Color changed to red")
                        elif finger_count == 3:
                            # Color change mode - three fingers up
                            color = (0, 255, 0)  # Green
                            print("Color changed to green")
                        elif finger_count == 4:
                            # Color change mode - four fingers up
                            color = (255, 0, 0)  # Blue
                            print("Color changed to blue")
                        else:
                            # Reset drawing position when not 1 or 5 fingers
                            # Also clear any partial drawing that might be stuck
                            global last_pos
                            last_pos = None
                            print("Drawing paused")
            except Exception as e:
                print(f"Error during hand detection: {e}")
        
        cv2.imshow("MyImage", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()