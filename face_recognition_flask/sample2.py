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
    attendance_data = []

    for date in dates:
        for roll in rolls:
            # Randomly generate attendance times between 8 AM and 4 PM (excluding absences)
            time = None if np.random.rand() > 0.1 else f"{np.random.randint(8, 16)}:{np.random.randint(0, 60):02d}"
            attendance_data.append([roll, time, date])

    df = pd.DataFrame(attendance_data, columns=['Roll', 'Time', 'Date'])
    return df

# Display the dashboard
def display_dashboard(attendance_df, student_df):
    st.markdown("<h1 style='text-align: center; color: #4CAF50; font-family: Arial, sans-serif;'>📋 Attendance Dashboard for students</h1>", unsafe_allow_html=True)
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

    # Year-wise Attendance by Department (New Chart)
    st.markdown("### 📊 **Year-wise Attendance by Department**")
    year_dept_summary = student_df.groupby(['Department', 'Year']).size().reset_index(name='Student Count')
    year_dept_fig = px.bar(year_dept_summary, x='Department', y='Student Count', color='Year', barmode='group',
                           labels={'Student Count': 'Number of Students', 'Department': 'Department'},
                           title="Year-wise Attendance by Department")
    st.plotly_chart(year_dept_fig, use_container_width=True)

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
