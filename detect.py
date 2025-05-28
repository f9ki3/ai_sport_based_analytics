import cv2
from ultralytics import YOLO
import numpy as np
import math
import json

# Load YOLOv8 pose model
model = YOLO("yolov8n-pose.pt")

# Input video
cap = cv2.VideoCapture("0528.mov")
if not cap.isOpened():
    print("Error opening video file")
    exit()

# Get video properties
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Use 'avc1' for H.264 encoding
fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Use 'mp4v' if 'avc1' fails
out = cv2.VideoWriter("save.mp4", fourcc, fps, (width, height))

# Court polygon
court_points = np.array([[228, 148], [633, 152], [782, 474], [63, 474]], np.int32).reshape((-1, 1, 2))

# Helper functions
def point_inside_court(cx, cy, polygon):
    return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def valid_point(pt):
    return pt[0] > 0 and pt[1] > 0 and not math.isnan(pt[0]) and not math.isnan(pt[1])

# Initialization
player_slot_to_id = {1: None, 2: None}
player_lost_counter = {1: 0, 2: 0}
last_keypoints = {}
MAX_MISSED_FRAMES = 20
frame_count = 0

player_stats = {
    1: {"total_smash_strength": 0, "smash_count": 0, "total_footwork": 0, "footwork_count": 0},
    2: {"total_smash_strength": 0, "smash_count": 0, "total_footwork": 0, "footwork_count": 0}
}

# Process video
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    cv2.polylines(frame, [court_points], isClosed=True, color=(255, 255, 0), thickness=2)
    results = model.track(source=frame, persist=True, classes=[0], iou=0.3, conf=0.3)
    visible_ids = []

    if results[0].boxes.id is not None:
        ids = results[0].boxes.id.int().cpu().tolist()
        boxes = results[0].boxes.xyxy.cpu().tolist()
        keypoints = results[0].keypoints.xy.cpu().tolist()

        for i, pid in enumerate(ids):
            x1, y1, x2, y2 = map(int, boxes[i])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if point_inside_court(cx, cy, court_points):
                visible_ids.append(pid)

                if player_slot_to_id[1] is None:
                    player_slot_to_id[1] = pid
                elif player_slot_to_id[2] is None and pid != player_slot_to_id[1]:
                    player_slot_to_id[2] = pid

                for slot, assigned_pid in player_slot_to_id.items():
                    if assigned_pid == pid:
                        color = (255, 0, 0) if slot == 1 else (0, 255, 0)
                        label = f"Player {slot}"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                        current_kps = keypoints[i]
                        prev_kps = last_keypoints.get(pid)

                        for point in current_kps:
                            if valid_point(point):
                                cv2.circle(frame, (int(point[0]), int(point[1])), 4, color, -1)

                        if prev_kps:
                            smash_speed = 0
                            if valid_point(current_kps[10]) and valid_point(prev_kps[10]):
                                smash_speed = distance(current_kps[10], prev_kps[10])
                            elif valid_point(current_kps[9]) and valid_point(prev_kps[9]):
                                smash_speed = distance(current_kps[9], prev_kps[9])

                            if smash_speed > 0:
                                player_stats[slot]["total_smash_strength"] += smash_speed
                                player_stats[slot]["smash_count"] += 1

                            foot_speed = 0
                            ankle_valid = False
                            if valid_point(current_kps[15]) and valid_point(prev_kps[15]):
                                foot_speed += distance(current_kps[15], prev_kps[15])
                                ankle_valid = True
                            if valid_point(current_kps[16]) and valid_point(prev_kps[16]):
                                foot_speed += distance(current_kps[16], prev_kps[16])
                                ankle_valid = True

                            if ankle_valid:
                                player_stats[slot]["total_footwork"] += foot_speed
                                player_stats[slot]["footwork_count"] += 1

                            cv2.putText(frame, f"Smash: {smash_speed:.1f}", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                            cv2.putText(frame, f"Footwork: {foot_speed:.1f}", (x1, y2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                        last_keypoints[pid] = current_kps

    # Handle player disappearance
    for slot in [1, 2]:
        pid = player_slot_to_id[slot]
        if pid is not None and pid not in visible_ids:
            player_lost_counter[slot] += 1
            if player_lost_counter[slot] >= MAX_MISSED_FRAMES:
                player_slot_to_id[slot] = None
                player_lost_counter[slot] = 0
        else:
            player_lost_counter[slot] = 0

    out.write(frame)
    print(f"\rProcessing: {(frame_count / total_frames) * 100:.2f}%", end="")

# Final stats
max_smash_speed = 50.0
max_foot_speed = 30.0
final_stats = {}

for player_id in [1, 2]:
    p = player_stats[player_id]
    avg_smash = p["total_smash_strength"] / p["smash_count"] if p["smash_count"] > 0 else 0
    avg_foot = p["total_footwork"] / p["footwork_count"] if p["footwork_count"] > 0 else 0
    final_stats[f"Player_{player_id}"] = {
        "average_smash_strength": round(avg_smash, 2),
        "average_smash_strength_percentage": round(min((avg_smash / max_smash_speed) * 100, 100), 2),
        "average_footwork": round(avg_foot, 2),
        "average_footwork_percentage": round(min((avg_foot / max_foot_speed) * 100, 100), 2),
    }

# Release resources
print("\nDone. Video saved as save.mp4")
print(json.dumps(final_stats, indent=4))
cap.release()
out.release()
