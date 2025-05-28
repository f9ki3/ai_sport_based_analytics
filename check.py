import cv2

# Load the first frame from the video
cap = cv2.VideoCapture("test1.mov")
ret, frame = cap.read()
cap.release()

if not ret:
    print("Failed to load video.")
    exit()

# Store clicked points
points = []

# Mouse click callback
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point {len(points)}: ({x}, {y})")
        if len(points) == 2:
            # Draw rectangle
            cv2.rectangle(frame, points[0], points[1], (255, 255, 0), 2)
            cv2.imshow("Select Court", frame)

# Show the first frame
cv2.imshow("Select Court", frame)
cv2.setMouseCallback("Select Court", click_event)

print("Click TOP-LEFT corner, then BOTTOM-RIGHT corner of the court area.")
cv2.waitKey(0)
cv2.destroyAllWindows()

# Output the final values
if len(points) == 2:
    (x1, y1), (x2, y2) = points
    court_x1, court_y1 = min(x1, x2), min(y1, y2)
    court_x2, court_y2 = max(x1, x2), max(y1, y2)
    print("\n🎯 Final Court Coordinates:")
    print(f"court_x1, court_y1 = {court_x1}, {court_y1}")
    print(f"court_x2, court_y2 = {court_x2}, {court_y2}")
else:
    print("You need to click two points to define the court.")
