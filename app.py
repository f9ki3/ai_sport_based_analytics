from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app 
app = Flask(__name__)
from models import *
from flask import session
import re
import cv2
from ultralytics import YOLO
import numpy as np
import math
import json
import tempfile
import os
from datetime import datetime
import random
import string

#For security of authentication this is secret key of the session for login
app.secret_key = 'a12sadsdsahasaafsdaqwegasd'

#YOLO model initialization
model = YOLO("yolov8n-pose.pt")

#route to analyze and detect badminton player performance from uploaded video
@app.route('/process_video', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400
    #check if video already exists
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Ensure save directory exists
    save_dir = os.path.join(current_app.root_path, 'static', 'save')
    os.makedirs(save_dir, exist_ok=True)

    # Save uploaded video to static/save with a safe unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    filename = f"input_{timestamp}_{random_str}.mp4"
    input_path = os.path.join(save_dir, filename)
    video_file.save(input_path)

    # Output filename similarly unique
    output_filename = f"output_{timestamp}_{random_str}.mp4"
    output_path = os.path.join(save_dir, output_filename)

    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            os.remove(input_path)
            return jsonify({"error": "Error opening video file"}), 500

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        court_points = np.array([[228, 148], [633, 152], [782, 474], [63, 474]], np.int32).reshape((-1, 1, 2))

        def point_inside_court(cx, cy, polygon):
            return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0

        def distance(p1, p2):
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

        def valid_point(pt):
            return pt[0] > 0 and pt[1] > 0 and not math.isnan(pt[0]) and not math.isnan(pt[1])

        player_slot_to_id = {1: None, 2: None}
        player_lost_counter = {1: 0, 2: 0}
        last_keypoints = {}
        MAX_MISSED_FRAMES = 20
        frame_count = 0

        player_stats = {
            1: {"total_smash_strength": 0, "smash_count": 0, "total_footwork": 0, "footwork_count": 0},
            2: {"total_smash_strength": 0, "smash_count": 0, "total_footwork": 0, "footwork_count": 0}
        }

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

        cap.release()
        out.release()

        # Return stats and URL to saved processed video
        video_url = f"/static/save/{output_filename}"
        Performance.insertPerformance(
            video_url,
            json.dumps(final_stats),  # Convert final_stats to a JSON string
            session.get("user_id")
        )
        data = {"stats": final_stats, "processed_video_url": video_url}
        return render_template('/pages/results.html', data=data)
    
        # data = '''
        # {
        # "processed_video_url": "/static/save/output_20250529101806_zFqDfY.mp4",
        # "stats": {
        #     "Player_1": {
        #     "average_footwork": 13.65,
        #     "average_footwork_percentage": 45.5,
        #     "average_smash_strength": 8.16,
        #     "average_smash_strength_percentage": 16.31
        #     },
        #     "Player_2": {
        #     "average_footwork": 11.33,
        #     "average_footwork_percentage": 37.77,
        #     "average_smash_strength": 7.25,
        #     "average_smash_strength_percentage": 14.51
        #     }
        # }
        # }
        # '''
        # parsed_data = json.loads(data)
        # return render_template('/pages/results.html', data=parsed_data)

    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({"error": str(e)}), 500
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/404.html"), 404

# This are the routes or links of different pages in the application
@app.route('/')
def root():
    return render_template('/pages/index.html')

@app.route('/login')
def login():
    return render_template('/pages/login.html')

@app.route('/register')
def register():
    return render_template('/pages/register.html')

@app.route('/scan')
def scan():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/scan.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    id  = session.get('user_id')
    result = Users.getUserById(id)
    return render_template('/pages/settings.html', data=result)

@app.route('/tips')
def tips():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/tips.html')

@app.route('/view_tips')
def view_tips():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/view_tips.html')


@app.route('/insights')
def insights():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    id = session.get('user_id')
    name = Users.getUserById(id)
    data = Performance.getPerformandashboard(id)
    return render_template('/pages/insights.html', data=data, name=name)

@app.route('/view/<int:id>')
def view(id):
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))

    performance = Performance.getPerformanceById(id)

    return render_template('/pages/view.html', data=performance)


@app.route('/history')
def history():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    id = session.get('user_id')
    data = Performance.getPerformanceByUserId(id)
    return render_template('/pages/history.html', data=data)

# Logout functionality
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#Registration
@app.route('/register_users', methods=['POST'])
def register_users():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    password = request.form.get('password')

    if not fullname or not email or not password:
        return redirect(url_for('/register'))  # redirect to your registration form page

    Users.insertUser(fullname, email, password)
    return render_template('/pages/success.html')

#login functionality
@app.route('/login_action', methods=['POST'])
def login_action():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('/pages/login.html', error="Email and password are required.")

    user = Users.login(email, password)
    if user:
        print(user)
        session['user_id'] = user['id']
        session['user_type'] = 'users'  # Assuming 'type' is a field in the user data
        return redirect(url_for('scan'))
    else:
        return render_template('/pages/login.html', error=1)

#update personal information
@app.route('/update_personal', methods=['POST'])
def update_personal():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    id = session.get('user_id')

    if not fullname or not email:
        return render_template('/pages/settings.html', error="All fields are required.")

    Users.updateUser(id, fullname, email)
    result = Users.getUserById(id)
    return render_template('/pages/settings.html', message=1, data=result)

#update password
@app.route('/update_password', methods=['POST'])
def update_password():
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    user_id = session.get('user_id')

    if not new_password or not confirm_password:
        result = Users.getUserById(user_id)
        return render_template('/pages/settings.html', message=5, data=result)

    if new_password != confirm_password:
        result = Users.getUserById(user_id)
        return render_template('/pages/settings.html', message=3, data=result)

    # if len(new_password) < 8 or not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
    #     result = Users.getUserById(user_id)
    #     return render_template('/pages/settings.html', message=4, data=result)

    Users.updatePassword(user_id, new_password)
    result = Users.getUserById(user_id)
    return render_template('/pages/settings.html', message=2, data=result)


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)