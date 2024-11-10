import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Generate Sample Student Data with the new list of students
def generate_sample_student_data():
    data = {
        'Roll': [101, 102, 103, 104, 105, 106, 107],
        'Name': ['Kovendhan', 'Kathiravan', 'Ranjith Raja', 'Mohamed Fahim', 'Murfith', 'Kamalesh', 'Bejisto Joseph'],
        'Department': ['IT', 'ECE', 'CSE', 'CSE', 'IT', 'CSE', 'ECE'],
        'Year': [3, 3, 3, 2, 1, 3, 2],
        'ParentEmail': ['kovendhan@example.com', 'kathiravan@example.com', 'ranjithraja@example.com', 
                        'mohamedfahim@example.com', 'murfith@example.com', 'kamalesh@example.com', 'bejisto@example.com']
    }
    return pd.DataFrame(data)

# Generate Sample Attendance Data (Date range 01-11-2024 to 07-11-2024)
def generate_sample_attendance_data():
    dates = pd.date_range(start="2024-11-01", end="2024-11-07", freq="D")
    rolls = [101, 102, 103, 104, 105, 106, 107]
    location = "Jeppiaar Nagar Kunnam Village, Sriperumbudur Taluk, Kanchipuram, Tamil Nadu 6316"
    attendance_data = []

    for date in dates:
        for roll in rolls:
            # Randomly generate attendance times between 8 AM and 4 PM (excluding absences)
            time = None if np.random.rand() > 0.2 else f"{np.random.randint(8, 16)}:{np.random.randint(0, 60):02d}"
            attendance_data.append([roll, time, date, location])

    df = pd.DataFrame(attendance_data, columns=['Roll', 'Time', 'Date', 'Location'])
    return df

# Track and notify long absences (Mock logic for sample)
def long_absence_notification(attendance_df, student_df):
    today = datetime.now().date()
    ten_days_ago = today - timedelta(days=10)
    
    # Ensure both Date column and ten_days_ago are of the same type for comparison
    attendance_df['Date'] = pd.to_datetime(attendance_df['Date']).dt.date  # Convert 'Date' to datetime.date
    
    recent_absences = attendance_df[attendance_df['Date'] >= ten_days_ago]
    absent_students = recent_absences.groupby('Roll').filter(lambda x: x['Time'].isnull().sum() >= 10)

    notification_sent = False
    for student_roll in absent_students['Roll'].unique():
        student_info = student_df[student_df['Roll'] == student_roll]
        if not student_info.empty:
            student_name = student_info['Name'].values[0]
            # Report to Ranjith Raja's parent (simulating email)
            if student_name == "Ranjith Raja":
                st.markdown(f"### 🚨 **Notification Sent**")
                st.markdown(f"**Ranjith Raja** has been absent for 10 days. An email has been sent to their parent.")
                # Here we simulate an email notification (no real email sending in this example)
                print(f"Sending email to {student_info['ParentEmail'].values[0]} about Ranjith Raja being absent for 10 days.")
            notification_sent = True
    return notification_sent

# Display the dashboard
def display_dashboard(attendance_df, student_df):
    # Report the absence (check for students absent for 10 days)
    long_absence_notification(attendance_df, student_df)

    st.markdown("<h1 style='text-align: center; color: #4CAF50; font-family: Arial, sans-serif;'>📋 Attendance Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Tracking attendance from 01-11-2024 to 07-11-2024</h3>", unsafe_allow_html=True)

    # Department-wise Attendance Summary (Synthetic Data)
    attendance_with_dept = attendance_df.merge(student_df[['Roll', 'Name', 'Department']], on='Roll', how='left')
    unique_dates = attendance_df['Date'].nunique()
    total_attendees = attendance_with_dept['Name'].nunique()
    total_present = attendance_with_dept[attendance_with_dept['Time'].notnull()]['Name'].nunique()

    # Display basic metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Unique Days", unique_dates, help="The number of days attendance was recorded.")
    col2.metric("👥 Unique Attendees", total_attendees, help="The number of unique students who attended.")
    col3.metric("✅ Total Present", total_present, help="The total number of students marked as present.")

    # Attendance by Date Chart
    st.markdown("### 📊 **Attendance Over Time**")
    date_summary = attendance_df.groupby('Date').size()
    date_fig = px.line(date_summary, x=date_summary.index, y=date_summary.values, labels={'x': 'Date', 'y': 'Attendance Count'}, title="Attendance Over Time")
    st.plotly_chart(date_fig, use_container_width=True)

    # Attendance by Department Chart
    st.markdown("### 📊 **Attendance by Department**")
    dept_summary = attendance_with_dept['Department'].value_counts().reset_index()
    dept_summary.columns = ['Department', 'Attendance Count']
    dept_fig = px.bar(dept_summary, x='Department', y='Attendance Count', title="Attendance by Department")
    st.plotly_chart(dept_fig, use_container_width=True)

    # Attendance Summary by Department (Unique Students)
    st.markdown("### 📊 **Unique Students by Department**")
    summary_chart = attendance_with_dept.groupby('Department')['Name'].nunique().reset_index()
    summary_chart.columns = ['Department', 'Unique Students']
    summary_fig = px.bar(summary_chart, x='Department', y='Unique Students', title="Unique Students by Department", color='Department')
    st.plotly_chart(summary_fig, use_container_width=True)

    # Attendance Summary by Student (Present vs Absent)
    st.markdown("### 📊 **Attendance Summary by Student**")
    attendance_with_names = attendance_df.merge(student_df[['Roll', 'Name']], on='Roll', how='left')
    attendance_summary = attendance_with_names.groupby(['Roll', 'Name']).agg(
        Present=('Time', lambda x: x.notnull().sum()), 
        Absent=('Time', lambda x: x.isnull().sum())
    ).reset_index()

    attendance_summary_fig = px.bar(attendance_summary, x='Name', y=['Present', 'Absent'], title="Attendance Summary by Student", barmode='stack')
    st.plotly_chart(attendance_summary_fig, use_container_width=True)

    # Peak Attendance Times Chart (Hour-wise)
    st.markdown("### 📊 **Peak Attendance Times**")
    attendance_df['Hour'] = pd.to_datetime(attendance_df['Time'], errors='coerce').dt.hour
    hour_summary = attendance_df['Hour'].dropna().value_counts().sort_index()
    time_fig = go.Figure(go.Bar(x=hour_summary.index, y=hour_summary.values, marker_color="#4CAF50"))
    time_fig.update_layout(title="Peak Attendance Hours", xaxis_title="Hour of the Day", yaxis_title="Number of Attendees", xaxis=dict(dtick=1))
    st.plotly_chart(time_fig, use_container_width=True)

    # Detailed Attendance Data
    st.markdown("### 📝 **Detailed Attendance Data**")
    st.dataframe(attendance_df)

    st.markdown("### 💾 **Download Full Attendance Data**")
    st.download_button("Download Full Attendance CSV", data=attendance_df.to_csv(index=False), file_name='Full_Attendance_Data.csv', mime='text/csv')

# Main
if __name__ == "__main__":
    student_df = generate_sample_student_data()
    attendance_df = generate_sample_attendance_data()
    display_dashboard(attendance_df, student_df)
