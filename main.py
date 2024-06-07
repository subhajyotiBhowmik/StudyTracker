from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from googleapiclient.discovery import build
from flask_mail import Mail, Message
import hashlib
import json
import os
import random
import string
import subprocess
import io
import sys
from datetime import datetime
import cv2
import numpy as np
import time
import threading

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'subhajyoti010102@gmail.com'  # Enter your Gmail address
app.config['MAIL_PASSWORD'] = 'vkps mwjm dnat voyd'   # Enter your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'subhajyoti010102@gmail.com'  # Enter your Gmail address

mail = Mail(app)

user_data = {
    'user1@example.com': {
        'password': 'password123'
    }
}

API_KEY = 'AIzaSyA95wDCTBxnMufuCbNS5e0sZyGbsdWjZC0'
youtube = build('youtube', 'v3', developerKey=API_KEY)

# In-memory store for notes and study tracker data
tracker_data = {
    'total_hours': 0,
    'sessions': 0,
    'time_spent': {
        'home': 0,
        'notes': 0,
        'videos': 0,
        'tracker': 0,
        'settings': 0
    }
}

# Secret key for session management
app.secret_key = b"27287817818jnjau7yqw821u12u"

# Function to hash password with SHA-256
def hash_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode())
    return sha256_hash.hexdigest()

# Function to load user data from JSON file
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as file:
            return json.load(file)
    else:
        return {}

# Function to save user data to JSON file
def save_users(users_data):
    with open('users.json', 'w') as file:
        json.dump(users_data, file)

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/videos', methods=['GET'])
def videos():
    query = request.args.get('query', 'study')
    videos = fetch_videos(query)
    return render_template('videos.html', videos=videos)

@app.route('/notes', methods=['GET', 'POST'])
def notes_route():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user = session['username']
        users_data = load_users()
        users_data[user]['notes'].append({'title': title, 'content': content})
        save_users(users_data)
        return redirect(url_for('notes_route'))

    user_notes = load_users().get(session['username'], {}).get('notes', [])
    return render_template('notes.html', notes=user_notes)

@app.route('/tracker', methods=['GET', 'POST'])
def study_tracker():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        hours = int(request.form['hours'])
        sessions = int(request.form['sessions'])
        tracker_data['total_hours'] += hours
        tracker_data['sessions'] += sessions
        return redirect(url_for('study_tracker'))
    return render_template('tracker.html', tracker_data=tracker_data)

@app.route('/compiler', methods=['GET', 'POST'])
def compiler():
    if request.method == 'GET':
        return render_template('compiler.html')
    elif request.method == 'POST':
        result = None
        try:
            code = request.form['code']
            language = request.form['language']
            if language == 'python':
                result = compile_python(code)
            elif language == 'java':
                result = compile_java(code)
            elif language == 'c':
                result = compile_c(code)
            elif language == 'cpp':
                result = compile_cpp(code)
            else:
                result = {"error": "Unsupported language."}
        except KeyError as e:
            result = {"error": f"Missing required field: {e}"}
        except Exception as e:
            result = {"error": f"An error occurred: {str(e)}"}
        return jsonify(result)

def compile_python(code):
    try:
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        exec(code)
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        return {"output": f"Compilation successful.\n\nOutput:\n{output}"}
    except Exception as e:
        return {"error": f"Error during compilation: {str(e)}"}

def compile_java(code):
    try:
        with open('Main.java', 'w') as f:
            f.write(code)
        result = subprocess.run(['javac', 'Main.java'], capture_output=True, text=True)
        if result.returncode == 0:
            execution_result = subprocess.run(['java', 'Main'], capture_output=True, text=True)
            output = execution_result.stdout
            return {"output": f"Compilation successful.\n\nOutput:\n{output}"}
        else:
            return {"error": f"Compilation failed:\n{result.stderr}"}
    except Exception as e:
        return {"error": f"Error during compilation: {str(e)}"}

def compile_c(code):
    try:
        with open('main.c', 'w') as f:
            f.write(code)
        result = subprocess.run(['gcc', 'main.c', '-o', 'main'], capture_output=True, text=True)
        if result.returncode == 0:
            execution_result = subprocess.run(['./main'], capture_output=True, text=True)
            output = execution_result.stdout
            return {"output": f"Compilation successful.\n\nOutput:\n{output}"}
        else:
            return {"error": f"Compilation failed:\n{result.stderr}"}
    except Exception as e:
        return {"error": f"Error during compilation: {str(e)}"}

def compile_cpp(code):
    try:
        with open('main.cpp', 'w') as f:
            f.write(code)
        result = subprocess.run(['g++', 'main.cpp', '-o', 'main'], capture_output=True, text=True)
        if result.returncode == 0:
            execution_result = subprocess.run(['./main'], capture_output=True, text=True)
            output = execution_result.stdout
            return {"output": f"Compilation successful.\n\nOutput:\n{output}"}
        else:
            return {"error": f"Compilation failed:\n{result.stderr}"}
    except Exception as e:
        return {"error": f"Error during compilation: {str(e)}"}

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('settings.html')

@app.route('/live_class')
def live_class():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('live_class.html')

@app.route('/schedule_class', methods=['POST'])
def schedule_class():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    data = request.json
    platform = data.get('platform')
    meeting_id = data.get('meeting_id')
    date_time_str = data.get('date_time')

    try:
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        # Save the meeting details to the database
        # Example: db.save_meeting(session['username'], platform, meeting_id, date_time)
        return jsonify({'status': 'success', 'message': 'Class scheduled successfully'})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date-time format'})

@app.route('/join_class', methods=['POST'])
def join_class():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    data = request.json
    platform = data.get('platform')
    meeting_id = data.get('meeting_id')

    # Retrieve meeting details from the database based on meeting ID
    # Example: meeting_details = db.get_meeting_by_id(meeting_id)

    # Redirect user to the platform's join page with the meeting ID
    if platform == 'zoom':
        return redirect(f'https://zoom.us/j/{meeting_id}')
    elif platform == 'google_meet':
        return redirect(f'https://meet.google.com/{meeting_id}')
    else:
        return jsonify({'status': 'error', 'message': 'Unsupported platform'})

@app.route('/track_time', methods=['POST'])
def track_time():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'})

    data = request.json
    section = data.get('section')
    time_spent = data.get('time_spent', 0)
    if section in tracker_data['time_spent']:
        tracker_data['time_spent'][section] += time_spent
    return jsonify({'status': 'success'})

def fetch_videos(query):
    request = youtube.search().list(
        part='snippet',
        q=query,
        maxResults=10,
        type='video'
    )
    response = request.execute()
    videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        embed_url = f'https://www.youtube.com/embed/{video_id}'
        videos.append({'title': item['snippet']['title'], 'embed_url': embed_url})
    return videos

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users_data = load_users()
        if username in users_data:
            hashed_password = users_data[username]['password']
            if hashed_password == hash_password(password):
                session['username'] = username
                return redirect(url_for('home'))
        return render_template('login.html', message='Invalid username or password')
    return render_template('login.html')

def generate_otp():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Route for Forgot Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        print("User Data:", user_data)  # Debugging
        if email in user_data:
            otp = generate_otp()
            user_data[email]['otp'] = otp
            send_otp_email(email, otp)  # Send OTP email
            return redirect(url_for('verify_otp', email=email))
        else:
            return render_template('forgot_password.html', message="Email not found.")
    return render_template('forgot_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email')
    if request.method == 'POST':
        otp_entered = request.form['otp']
        if email in user_data and 'otp' in user_data[email] and user_data[email]['otp'] == otp_entered:
            return redirect(url_for('reset_password', email=email))
        else:
            return render_template('verify_otp.html', message="Invalid OTP. Please try again.")
    return render_template('verify_otp.html')

def age_estimator():
    # Capture Image from Webcam
    cap = cv2.VideoCapture(1)
    start_time = time.time()
    age = "Unknown"
    while time.time() - start_time < 3:  # Capture frames for 3 seconds
        ret, frame = cap.read()
        if ret:
            # Process the image to eastimate age
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                x, y, w, h = faces[0]
                roi_gray = gray[y:y + h, x:x + w]
                age_net = cv2.dnn.readNetFromCaffe('deploy_age.prototxt', 'age_net.caffemodel')
                MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
                blob = cv2.dnn.blobFromImage(roi_gray, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                age_net.setInput(blob)
                preds = age_net.forward()
                age = int(preds[0].dot(np.arange(0, 101).reshape(101, 1)))
            # Display age on the frame
            cv2.putText(frame, f'Age: {age}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            # Show the frame
            cv2.imshow('Age Estimation', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()
    return age

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password == confirm_password:
            user_data[email]['password'] = new_password
            return "Password changed successfully!"
        else:
            return render_template('reset_password.html', message="Passwords do not match.")
    return render_template('reset_password.html')


def generate_otp():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_otp_email(email, otp):
    msg = Message('Password Reset OTP', recipients=[email])
    msg.body = f'Your OTP for password reset is: {otp}'
    mail.send(msg)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        age_thread = threading.Thread(target=age_estimator)
        age_thread.start()
        age_thread.join()
        users_data = load_users()
        if username not in users_data:
            hashed_password = hash_password(password)
            users_data[username] = {'password': hashed_password, 'notes': []}
            save_users(users_data)
            return redirect(url_for('login'))
        else:
            return render_template('signup.html', message='Username already exists')


    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True,host='100.20.92.101',port=8000)