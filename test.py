'''import cv2
from pyzbar.pyzbar import decode

# Function to scan and decode QR codes
def scan_qr_code(frame):
    # Decode the QR code/barcode in the frame
    decoded_objects = decode(frame)

    for obj in decoded_objects:
        # Draw a bounding box around the detected QR code
        points = obj.polygon

        # Convert the points into a rectangle if there are more than 4 points
        if len(points) > 4:
            hull = cv2.convexHull(points)
            points = hull.reshape((-1, 2))
        
        # Draw lines around the QR code
        n = len(points)
        for j in range(n):
            cv2.line(frame, tuple(points[j]), tuple(points[(j+1) % n]), (0, 255, 0), 3)

        # Display the decoded text
        qr_data = obj.data.decode("utf-8")
        cv2.putText(frame, qr_data, (points[0][0], points[0][1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        print(f"QR Code Detected: {qr_data}")
    
    return frame

# Open the webcam (index 0 is the default webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Continuously capture frames from the webcam
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # Scan for QR codes in the current frame
    frame = scan_qr_code(frame)

    # Display the frame
    cv2.imshow('QR Code Scanner', frame)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()'''

import streamlit as st
import base64
import requests
from PIL import Image
import io

# Title of the app
st.title("Universal Camera Access for Mobile and Laptops")

# Custom HTML and JavaScript for capturing image from the rear camera (fallback to front camera if unavailable)
custom_js = """
    <video id="video" width="100%" height="100%" autoplay></video>
    <button id="capture" style="margin-top: 10px;">Capture Frame</button>
    <script>
        const video = document.getElementById('video');

        // Try to access the rear camera (on mobile), or fallback to front/default camera (on laptops)
        const constraints = {
            video: { facingMode: { ideal: "environment" } }  // 'ideal' tries back camera first, but falls back
        };

        // Request camera stream
        navigator.mediaDevices.getUserMedia(constraints)
            .then((stream) => {
                video.srcObject = stream;  // Display video stream in the <video> element
            })
            .catch((err) => {
                console.error('Error accessing the camera, switching to default camera:', err);

                // If rear camera isn't available, fall back to default (front) camera
                const fallbackConstraints = { video: true };
                navigator.mediaDevices.getUserMedia(fallbackConstraints)
                    .then((stream) => {
                        video.srcObject = stream;
                    })
                    .catch((err) => {
                        console.error('Error accessing the default camera:', err);
                    });
            });

        // Capture the frame when the button is clicked
        const captureButton = document.getElementById('capture');
        captureButton.onclick = () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert the captured frame to a Base64 string
            const dataURL = canvas.toDataURL('image/jpeg');

            // Send the captured image data to Streamlit for further processing
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/upload_image", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify({ image: dataURL }));
        };
    </script>
"""

# Step 3: Display the HTML with JavaScript inside the Streamlit app
st.components.v1.html(custom_js, height=500)

# Step 4: If the image is captured and sent, process it
if "image" in st.session_state:
    # Decode the base64 image stored in session_state
    img_data = base64.b64decode(st.session_state["image"].split(",")[1])
    image = Image.open(io.BytesIO(img_data))

    # Display the captured image in the Streamlit app
    st.image(image, caption="Captured Image")

    # Option to send the image to an API or save it
    if st.button("Send Image for Processing"):
        url = "http://127.0.0.1:5000/process_image"  # Update with your API endpoint
        response = requests.post(url, json={"image": st.session_state["image"]})

        if response.status_code == 200:
            st.write("Processing completed:")
            st.json(response.json())  # Display the response from the server
        else:
            st.error(f"Error: {response.status_code}")
