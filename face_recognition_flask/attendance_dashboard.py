import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import smtplib

# Load attendance data from multiple CSV files
def load_attendance_data():
    all_data = []
    for file in os.listdir('Attendance'):
        if file.endswith('.csv'):
            try:
                date_str = file.split('-')[1].split('.')[0]  # Format: Attendance-MM_DD_YY.csv
                date = datetime.strptime(date_str, '%m_%d_%y').date()
                df = pd.read_csv(f'Attendance/{file}')
                df['Date'] = date
                df['Location'] = "Jeppiaar Nagar, Kunnam Village, Sriperumbudur Taluk, Kanchipuram, Tamil Nadu 631604"
                all_data.append(df)
            except ValueError:
                print(f"Filename format error for: {file}")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

# Load student data
def load_student_data():
    return pd.read_csv('studentlist.csv')

# Send email notifications
def send_email(to_email, subject, body):
    sender_email = "mohamedfahim786skt@gmail.com"
    sender_password = "MohamedFahim786786"
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Change SMTP server
            server.login(sender_email, sender_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, to_email, message)
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False

# Track and notify long absences
def long_absence_notification(attendance_df, student_df):
    today = datetime.now().date()
    ten_days_ago = today - timedelta(days=10)
    recent_absences = attendance_df[attendance_df['Date'] >= ten_days_ago]
    absent_students = recent_absences.groupby('Roll').filter(lambda x: x['Time'].isnull().sum() >= 10)
    
    notification_sent = False
    for student_roll in absent_students['Roll'].unique():
        student_info = student_df[student_df['Roll'] == student_roll]
        if not student_info.empty:
            parent_email = student_info['ParentEmail'].values[0]
            student_name = student_info['Name'].values[0]
            email_sent = send_email(
                to_email=parent_email,
                subject="10-Day Absence Alert",
                body=f"Dear Parent, your child {student_name} has been absent for 10 consecutive days."
            )
            if email_sent:
                notification_sent = True
    return notification_sent

# Display dashboard
def display_dashboard(attendance_df, student_df):
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📋 Attendance Dashboard</h1>", unsafe_allow_html=True)
    unique_dates = attendance_df['Date'].nunique()
    total_attendees = attendance_df['Name'].nunique()
    total_present = attendance_df[attendance_df['Time'].notnull()]['Name'].nunique()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Unique Days", unique_dates)
    col2.metric("👥 Unique Attendees", total_attendees)
    col3.metric("✅ Total Present", total_present)

    # Check for long absences and send notifications if necessary
    notification_sent = long_absence_notification(attendance_df, student_df)
    if notification_sent:
        st.markdown("### Long Absences Notification Sent")
    else:
        st.markdown("### All students are properly attending classes")

    st.markdown("### Attendance by Date")
    date_summary = attendance_df.groupby('Date').size()
    date_fig = px.line(date_summary, x=date_summary.index, y=date_summary.values, labels={'x': 'Date', 'y': 'Attendance Count'}, title="Attendance Over Time")
    st.plotly_chart(date_fig, use_container_width=True)

    st.markdown("### Attendance by Department")
    attendance_with_dept = attendance_df.merge(student_df, on='Roll', how='left')
    dept_summary = attendance_with_dept['Department'].value_counts().reset_index()
    dept_summary.columns = ['Department', 'Attendance Count']
    dept_fig = px.bar(dept_summary, x='Department', y='Attendance Count', title="Attendance by Department")
    st.plotly_chart(dept_fig, use_container_width=True)

    st.markdown("### Peak Attendance Times")
    attendance_df['Hour'] = pd.to_datetime(attendance_df['Time'], errors='coerce').dt.hour
    hour_summary = attendance_df['Hour'].dropna().value_counts().sort_index()
    time_fig = go.Figure(go.Bar(x=hour_summary.index, y=hour_summary.values, marker_color="#4CAF50"))
    time_fig.update_layout(title="Peak Attendance Hours", xaxis_title="Hour of the Day", yaxis_title="Number of Attendees", xaxis=dict(dtick=1))
    st.plotly_chart(time_fig, use_container_width=True)

    st.markdown("### Detailed Attendance Data")
    st.dataframe(attendance_df)

    st.markdown("### Download Attendance Data")
    st.download_button("Download Full Attendance CSV", data=attendance_df.to_csv(index=False), file_name='Full_Attendance_Data.csv', mime='text/csv')

# Main
if __name__ == "__main__":
    attendance_df = load_attendance_data()
    student_df = load_student_data()
    display_dashboard(attendance_df, student_df)
