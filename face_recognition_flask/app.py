from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from flask import Flask, request, render_template, redirect, url_for
import cv2
import os
from datetime import date, datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import joblib

app = Flask(__name__, template_folder="K:/New folder (3)/face_recognition_flask/templates")

nimgs = 10
imgBackground = cv2.imread("background.png")

datetoday = date.today().strftime("%m_%d_%y")
datetoday2 = date.today().strftime("%d-%B-%Y")

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Setup directories
if not os.path.isdir('Attendance'):
    os.makedirs('Attendance')
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')
if f'Attendance-{datetoday}.csv' not in os.listdir('Attendance'):
    with open(f'Attendance/Attendance-{datetoday}.csv', 'w') as f:
        f.write('Name,Roll,Time')

def totalreg():
    return len(os.listdir('static/faces'))

def extract_faces(img):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = face_detector.detectMultiScale(gray, 1.2, 5, minSize=(20, 20))
        return face_points
    except:
        return []

def identify_face(facearray):
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)

def train_model():
    faces = []
    labels = []
    userlist = os.listdir('static/faces')
    for user in userlist:
        for imgname in os.listdir(f'static/faces/{user}'):
            img = cv2.imread(f'static/faces/{user}/{imgname}')
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'static/face_recognition_model.pkl')

def extract_attendance():
    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    names = df['Name']
    rolls = df['Roll']
    times = df['Time']
    l = len(df)
    return names, rolls, times, l

def add_attendance(name):
    username = name.split('_')[0]
    userid = name.split('_')[1]
    current_time = datetime.now().strftime("%H:%M:%S")

    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    if int(userid) not in list(df['Roll']):
        with open(f'Attendance/Attendance-{datetoday}.csv', 'a') as f:
            f.write(f'\n{username},{userid},{current_time}')

def getallusers():
    userlist = os.listdir('static/faces')
    names = []
    rolls = []
    l = len(userlist)

    for i in userlist:
        name, roll = i.split('_')
        names.append(name)
        rolls.append(roll)

    return userlist, names, rolls, l

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        
        user_dir = f'static/faces/{name}_{roll}'
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        cap = cv2.VideoCapture(0)
        count = 0
        while count < nimgs:
            ret, frame = cap.read()
            if not ret:
                break
            
            faces = extract_faces(frame)
            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (50, 50))
                cv2.imwrite(f'{user_dir}/{count}.jpg', face_img)
                count += 1
                if count >= nimgs:
                    break

            cv2.imshow('Adding Face', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        # Retrain model after adding new user
        train_model()
        
        return redirect(url_for('home'))
    return render_template('add_user.html')

def update_csv(name, roll):
    current_time = datetime.now().strftime("%H:%M:%S")
    file_path = f'Attendance/Attendance-{datetoday}.csv'

    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('Name,Roll,Time\n')
    
    df = pd.read_csv(file_path)
    if roll not in df['Roll'].values:
        with open(file_path, 'a') as f:
            f.write(f'{name},{roll},{current_time}\n')

@app.route('/start', methods=['GET'])
def start_attendence():
    # Check time and start attendance
    names, rolls, times, l = extract_attendance()
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', message="Train a model first.")

    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            face_img = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face_img.reshape(1, -1))[0]
            name, roll = identified_person.split('_')
            update_csv(name, roll)

            # Display on screen
            cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow('Attendance', frame)
        if cv2.waitKey(1) == 27:  # Press 'Esc' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l)


@app.route('/')
def home():
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2)

# New route for taking attendance
@app.route('/take_attendance')
def take_attendance():
    return redirect(url_for('start'))

@app.route('/start', methods=['GET'])
def start_attendance():
    names, rolls, times, l = extract_attendance()

    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2, mess='There is no trained model in the static folder. Please add a new face to continue.')

    ret = True
    cap = cv2.VideoCapture(0)
    while ret:
        ret, frame = cap.read()
        if len(extract_faces(frame)) > 0:
            (x, y, w, h) = extract_faces(frame)[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
            face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face.reshape(1, -1))[0]
            add_attendance(identified_person)
            cv2.putText(frame, f'{identified_person}', (x, y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
        imgBackground[162:162 + 480, 55:55 + 640] = frame
        cv2.imshow('Attendance', imgBackground)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2)

# Other routes remain unchanged

# Initialize the Flask app and set a secret key for session management
app.secret_key = 'newkey'

# Define admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = generate_password_hash("admin123")

# Route for admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD, password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

# Route for the admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    names, rolls, times, l = extract_attendance()
    return render_template('admin_dashboard.html', names=names, rolls=rolls, times=times, l=l)

# Route for starting the attendance marking
@app.route('/start', methods=['GET'])
def start():
    current_hour = datetime.now().hour
    if not (8 <= current_hour < 16):
        message = "Attendance can only be marked between 8:00 AM and 4:00 PM."
        return render_template('home.html', message=message)
    
    # Retrieve attendance data
    names, rolls, times, count = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, count=count)

# Route for displaying attendance analytics
@app.route('/admin/analytics')
def attendance_analytics():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Example attendance data for demonstration
    df = pd.DataFrame({'Name': ["Alice", "Bob", "Charlie"], 'Time': ["08:00", "08:30", "09:00"]})
    attendance_counts = df['Name'].value_counts()

    # Generate and encode attendance plot
    plt.figure(figsize=(10, 6))
    attendance_counts.plot(kind='bar', color='skyblue')
    plt.title("Attendance Frequency")
    plt.xlabel("Names")
    plt.ylabel("Attendance Count")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()  # Close the plot to release memory

    return render_template('attendance_analytics.html', plot_url=plot_url)

# Route for admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# Mock function to extract attendance data
def extract_attendance():
    names = ["Alice", "Bob", "Charlie"]
    rolls = ["101", "102", "103"]
    times = ["08:00", "08:30", "09:00"]
    l = len(names)  # Ensure `l` is the same as the length of the lists
    return names, rolls, times, l


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
