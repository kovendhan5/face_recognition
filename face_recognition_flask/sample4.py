import cv2
import os
from flask import Flask, request, render_template
from datetime import date, datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import joblib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, template_folder="K:/New folder (3)/face_recognition_flask/templates")

# Constants
nimgs = 10
IP_WEBCAM_URL = "http://192.0.0.4:8080/video"  # Replace with your actual IP Webcam URL

# Load background image and face detector
imgBackground = cv2.imread("background.png")
face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Paths and file setup
datetoday = date.today().strftime("%m_%d_%y")
datetoday2 = date.today().strftime("%d-%B-%Y")

if not os.path.isdir('Attendance'):
    os.makedirs('Attendance')
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')
if f'Attendance-{datetoday}.csv' not in os.listdir('Attendance'):
    with open(f'Attendance/Attendance-{datetoday}.csv', 'w') as f:
        f.write('Name,Roll,Time\n')

# Load parent email data
parent_data = pd.read_csv('parents.csv')

# Utility Functions
def send_email_to_parent(student_name):
    parent_email = parent_data.loc[parent_data['Name'] == student_name, 'parentemail'].values
    if parent_email:
        email_address = parent_email[0]
        message = MIMEMultipart()
        message["Subject"] = "Attendance Notification"
        message["From"] = "your_email@example.com"  # Use your email
        message["To"] = email_address

        # Customize email content
        text = f"Dear Parent,\n\nThis is to notify you that your child {student_name} has been marked present today ({datetoday2})."
        message.attach(MIMEText(text, "plain"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("your_email@example.com", "your_email_password")  # Use your email credentials
                server.sendmail("your_email@example.com", email_address, message.as_string())
            print(f"Notification sent to {email_address}")
        except Exception as e:
            print(f"Error sending email: {e}")

def add_attendance(name):
    username = name.split('_')[0]
    roll = name.split('_')[1]  # Renamed userid to roll for consistency
    current_time = datetime.now().strftime("%H:%M:%S")

    # Load today's attendance CSV
    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    # Check if roll number is not already in today's attendance
    if int(roll) not in list(df['Roll']):
        with open(f'Attendance/Attendance-{datetoday}.csv', 'a') as f:
            f.write(f'\n{username},{roll},{current_time}')
        send_email_to_parent(username)  # Send email notification

def extract_attendance():
    today = datetime.today().strftime('%m_%d_%y')
    try:
        df = pd.read_csv(f'Attendance/Attendance-{today}.csv', on_bad_lines='skip')  # Skip bad lines
    except pd.errors.ParserError as e:
        print(f"Error reading file: Attendance/Attendance-{today}.csv - {e}")
        return [], [], [], False

    # Extract names, rolls, and times
    names = df['Name'].tolist()
    rolls = df['Roll'].tolist()
    times = df['Time'].tolist()
    
    return names, rolls, times, True

# Flask Routes
@app.route('/')
def home():
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2)

@app.route('/start', methods=['GET'])
def start():
    names, rolls, times, l = extract_attendance()

    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2, mess='No trained model available.')

    ret = True
    cap = cv2.VideoCapture(IP_WEBCAM_URL)
    while ret:
        ret, frame = cap.read()
        frame = cv2.resize(frame, (640, 480))

        if len(extract_faces(frame)) > 0:
            (x, y, w, h) = extract_faces(frame)[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
            face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face.reshape(1, -1))[0]
            add_attendance(identified_person)
            cv2.putText(frame, f'{identified_person}', (x, y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
        
        imgBackground[162:642, 55:695] = frame
        cv2.imshow('Attendance', imgBackground)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2)

# Placeholder function for total registered students
def totalreg():
    # You can implement this function to return the total number of registered students
    return 100

# Placeholder function to extract faces - replace with actual function if needed
def extract_faces(frame):
    # Implement the face extraction logic here
    return []

# Placeholder function to identify face - replace with actual function if needed
def identify_face(face_array):
    # Implement the face identification logic here
    return ["student_name_roll"]

if __name__ == '__main__':
    app.run(debug=True)
