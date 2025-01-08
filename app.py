import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
from typing import Optional, List, Dict, Any
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure page first, before any other Streamlit command
st.set_page_config(
    page_title="Hospital Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)


def safe_dataframe_check(df: pd.DataFrame) -> bool:
    """Safely check if DataFrame is empty"""
    if df is None:
        return False
    return not df.empty


def handle_error(error: Exception, context: str):
    """Centralized error handling"""
    error_message = str(error)
    logging.error(f"Error in {context}: {error_message}")

    if isinstance(error, pyodbc.Error):
        st.error(f"Database error: {error_message}")
    else:
        st.error(f"An error occurred: {error_message}")


# Configuration and Constants
class Config:
    PAGE_TITLE = "Hospital Management System"
    THEME_COLOR = "#2E86C1"
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?1?\d{9,15}$'



# Custom CSS with improved styling
st.markdown("""
    <style>
    /* Main Theme Colors */
    :root {
        --primary-color: #2E86C1;
        --secondary-color: #AED6F1;
        --accent-color: #1ABC9C;
        --background-color: #F8F9F9;
        --text-color: #2C3E50;
    }

    /* General Styling */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 2rem;
    }

    /* Header Styling */
    h1, h2, h3 {
        color: var(--primary-color);
        font-weight: 600;
        margin-bottom: 1.5rem;
    }

    /* Card Styling */
    .stCard {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    /* Button Styling */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 0.3rem;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: var(--accent-color);
        transform: translateY(-2px);
    }

    /* Status Indicators */
    .status-indicator {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 500;
    }

    .status-scheduled {
        background-color: #FEF9E7;
        color: #F1C40F;
    }

    .status-completed {
        background-color: #E8F8F5;
        color: #2ECC71;
    }

    .status-cancelled {
        background-color: #FDEDEC;
        color: #E74C3C;
    }

    /* Patient Card Styling */
    .patient-card {
        padding: 1rem;
        border: 1px solid #e1e4e8;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }

    .patient-card h4 {
        color: var(--primary-color);
        margin: 0;
    }

    /* Form Styling */
    .stTextInput>div>div>input {
        border-radius: 0.3rem;
    }

    .stSelectbox>div>div>select {
        border-radius: 0.3rem;
    }

    /* Table Styling */
    .dataframe {
        border: none !important;
    }

    .dataframe th {
        background-color: var(--primary-color);
        color: white;
        padding: 0.5rem !important;
    }

    .dataframe td {
        padding: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


# Database Connection Handler
class DatabaseConnection:
    @staticmethod
    def get_connection():
        try:
            return pyodbc.connect(
                "Driver={SQL Server};"
                "Server=DESKTOP-KA8OD8M\SQLEXPRESS;"
                "Database=SimpleHospitalDB;"
                "Trusted_Connection=yes;"
            )
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            return None

    @staticmethod
    def run_query(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        conn = None
        try:
            conn = DatabaseConnection.get_connection()
            if conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                data = cursor.fetchall()
                return pd.DataFrame.from_records(data, columns=columns)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Query execution error: {str(e)}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()

    @staticmethod
    def execute_query(query: str, params: Optional[tuple] = None) -> bool:
        conn = None
        try:
            conn = DatabaseConnection.get_connection()
            if conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return True
            return False
        except Exception as e:
            st.error(f"Query execution error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()

def execute_transaction(queries_and_params):
    """Execute multiple queries in a transaction"""
    conn = None
    try:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        for query, params in queries_and_params:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Error executing transaction: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

# Input Validation
class Validator:
    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(Config.EMAIL_PATTERN, email)) if email else True

    @staticmethod
    def validate_phone(phone: str) -> bool:
        return bool(re.match(Config.PHONE_PATTERN, phone)) if phone else True

    @staticmethod
    def validate_date(date: datetime) -> bool:
        return date <= datetime.now() if date else True


# UI Components
class UIComponents:
    @staticmethod
    def loading_spinner():
        with st.spinner('Loading...'):
            time.sleep(0.5)

    @staticmethod
    def success_message(message: str):
        st.success(message)
        time.sleep(2)
        st.experimental_rerun()

    @staticmethod
    def error_message(message: str):
        st.error(message)

    @staticmethod
    def create_metric_card(title: str, value: Any, delta: Optional[Any] = None):
        st.markdown(f"""
        <div class="stCard">
            <h4 style="margin-bottom: 0.5rem;">{title}</h4>
            <h2 style="margin: 0; color: var(--primary-color);">{value}</h2>
            {f'<p style="margin: 0; color: {"green" if delta > 0 else "red"};">{"↑" if delta > 0 else "↓"} {abs(delta)}%</p>' if delta is not None else ''}
        </div>
        """, unsafe_allow_html=True)


# Enhanced Navigation
def create_navigation():
    with st.sidebar:
        st.image("hospital_image.jpeg")
        st.title("Navigation")
        return st.radio(
            "Select Page",
            ["Dashboard", "Patients", "Doctors", "Appointments", "Admissions"],
            key="navigation"
        )


# Dashboard Functions
def get_patient_growth():
    """Calculate patient growth percentage compared to last month"""
    current_month = DatabaseConnection.run_query("""
        SELECT COUNT(*) as count 
        FROM Patient 
        WHERE MONTH(CreatedDate) = MONTH(GETDATE())
        AND YEAR(CreatedDate) = YEAR(GETDATE())
    """).iloc[0]['count']

    last_month = DatabaseConnection.run_query("""
        SELECT COUNT(*) as count 
        FROM Patient 
        WHERE MONTH(CreatedDate) = MONTH(DATEADD(MONTH, -1, GETDATE()))
        AND YEAR(CreatedDate) = YEAR(DATEADD(MONTH, -1, GETDATE()))
    """).iloc[0]['count']

    if last_month == 0:
        return 100 if current_month > 0 else 0
    return round(((current_month - last_month) / last_month) * 100, 1)


def show_patient_demographics():
    """Display patient demographics chart"""
    demographics = DatabaseConnection.run_query("""
        SELECT 
            g.Name as Gender,
            COUNT(*) as Count,
            AVG(DATEDIFF(YEAR, p.DateOfBirth, GETDATE())) as AvgAge
        FROM Patient p
        JOIN Gender g ON p.GenderID = g.GenderID
        GROUP BY g.Name
    """)

    if not demographics.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=demographics['Gender'],
            y=demographics['Count'],
            name='Count',
            text=demographics['Count'],
            textposition='auto',
        ))
        fig.add_trace(go.Scatter(
            x=demographics['Gender'],
            y=demographics['AvgAge'],
            name='Avg Age',
            yaxis='y2',
            line=dict(color='red'),
            mode='lines+markers'
        ))

        fig.update_layout(
            yaxis2=dict(
                title='Average Age',
                overlaying='y',
                side='right'
            ),
            barmode='group',
            height=400,
            title_text='Patient Demographics and Average Age',
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)


def show_department_distribution():
    """Display department distribution pie chart"""
    dept_data = DatabaseConnection.run_query("""
        SELECT 
            d.Name as Department,
            COUNT(doc.DoctorID) as DoctorCount,
            COUNT(DISTINCT a.PatientID) as PatientCount
        FROM Department d
        LEFT JOIN Doctor doc ON d.DepartmentID = doc.DepartmentID
        LEFT JOIN Appointment a ON doc.DoctorID = a.DoctorID
        GROUP BY d.Name
    """)

    if not dept_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=dept_data['Department'],
            values=dept_data['DoctorCount'],
            name='Doctors',
            domain={'x': [0, 0.47]},
            title='Doctors Distribution'
        ))
        fig.add_trace(go.Pie(
            labels=dept_data['Department'],
            values=dept_data['PatientCount'],
            name='Patients',
            domain={'x': [0.53, 1]},
            title='Patient Distribution'
        ))

        fig.update_layout(
            height=400,
            title_text='Department-wise Distribution',
            annotations=[
                dict(text='Doctors', x=0.19, y=0.5, showarrow=False, font_size=13),
                dict(text='Patients', x=0.81, y=0.5, showarrow=False, font_size=13)
            ]
        )

        st.plotly_chart(fig, use_container_width=True)


def show_recent_appointments():
    """Display recent appointments with enhanced styling"""
    appointments = DatabaseConnection.run_query("""
        SELECT TOP 5
            PatientName,
            DoctorName,
            AppointmentDate,
            Status,
            DATEDIFF(MINUTE, GETDATE(), AppointmentDate) as TimeUntil
        FROM vw_AppointmentDetails
        WHERE CAST(AppointmentDate AS DATE) >= CAST(GETDATE() AS DATE)
        ORDER BY AppointmentDate
    """)

    if not appointments.empty:
        for _, appt in appointments.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**Patient:** {appt['PatientName']}")
                    st.markdown(f"**Doctor:** {appt['DoctorName']}")
                with col2:
                    st.markdown(f"**Date:** {appt['AppointmentDate'].strftime('%Y-%m-%d %H:%M')}")
                    time_until = appt['TimeUntil']
                    if time_until > 0:
                        st.markdown(f"**Time Until:** {time_until // 60}h {time_until % 60}m")
                    else:
                        st.markdown("**Status:** Past due")
                with col3:
                    status_color = {
                        'Scheduled': 'status-scheduled',
                        'Completed': 'status-completed',
                        'Cancelled': 'status-cancelled'
                    }.get(appt['Status'], '')
                    st.markdown(f"<div class='status-indicator {status_color}'>{appt['Status']}</div>",
                                unsafe_allow_html=True)
                st.markdown("---")


def show_recent_admissions():
    """Display recent admissions with room details"""
    admissions = DatabaseConnection.run_query("""
        SELECT TOP 5
            PatientName,
            DoctorName,
            RoomNumber,
            RoomType,
            AdmissionDate,
            Status,
            DATEDIFF(DAY, AdmissionDate, GETDATE()) as DaysAdmitted
        FROM vw_AdmissionDetails
        WHERE Status = 'Admitted'
        ORDER BY AdmissionDate DESC
    """)

    if not admissions.empty:
        for _, adm in admissions.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**Patient:** {adm['PatientName']}")
                    st.markdown(f"**Doctor:** {adm['DoctorName']}")
                with col2:
                    st.markdown(f"**Room:** {adm['RoomNumber']} ({adm['RoomType']})")
                    st.markdown(f"**Admitted:** {adm['AdmissionDate'].strftime('%Y-%m-%d')}")
                with col3:
                    st.markdown(f"**Days:** {adm['DaysAdmitted']}")
                    st.markdown(f"**Status:** {adm['Status']}")
                st.markdown("---")


def show_room_status():
    """Display interactive room status visualization"""
    rooms = DatabaseConnection.run_query("""
        SELECT 
            RoomNumber,
            RoomType,
            Status,
            CASE 
                WHEN Status = 'Occupied' THEN
                    (SELECT TOP 1 p.FirstName + ' ' + p.LastName
                     FROM Admission a
                     JOIN Patient p ON a.PatientID = p.PatientID
                     WHERE a.RoomID = r.RoomID AND a.Status = 'Admitted')
                ELSE NULL
            END as CurrentPatient
        FROM Room r
        ORDER BY RoomType, RoomNumber
    """)

    if not rooms.empty:
        for room_type in rooms['RoomType'].unique():
            st.markdown(f"#### {room_type} Rooms")
            cols = st.columns(4)
            type_rooms = rooms[rooms['RoomType'] == room_type]

            for idx, (_, room) in enumerate(type_rooms.iterrows()):
                with cols[idx % 4]:
                    status_color = 'green' if room['Status'] == 'Available' else 'red'
                    st.markdown(
                        f"""
                        <div style="padding: 1rem; border: 1px solid {status_color}; 
                        border-radius: 0.5rem; margin-bottom: 1rem;">
                            <h4 style="margin: 0; color: {status_color};">
                                Room {room['RoomNumber']}
                            </h4>
                            <p style="margin: 0.5rem 0;">Status: {room['Status']}</p>
                            {f"<p style='margin: 0;'>Patient: {room['CurrentPatient']}</p>"
                        if room['CurrentPatient'] else ""}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


def show_dashboard():
    """Main dashboard display function"""
    st.title("Hospital Dashboard")

    with st.spinner("Loading dashboard data..."):
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_patients = DatabaseConnection.run_query(
                "SELECT COUNT(*) as count FROM Patient"
            ).iloc[0]['count']
            UIComponents.create_metric_card(
                "Total Patients",
                f"{total_patients:,}",
                get_patient_growth()
            )

        with col2:
            today_appointments = DatabaseConnection.run_query("""
                SELECT COUNT(*) as count 
                FROM Appointment 
                WHERE CAST(AppointmentDate AS DATE) = CAST(GETDATE() AS DATE)
            """).iloc[0]['count']
            UIComponents.create_metric_card(
                "Today's Appointments",
                today_appointments
            )

        with col3:
            current_admissions = DatabaseConnection.run_query("""
                SELECT COUNT(*) as count 
                FROM Admission 
                WHERE Status = 'Admitted'
            """).iloc[0]['count']
            UIComponents.create_metric_card(
                "Current Admissions",
                current_admissions
            )

        with col4:
            available_rooms = DatabaseConnection.run_query("""
                SELECT COUNT(*) as count 
                FROM Room 
                WHERE Status = 'Available'
            """).iloc[0]['count']
            UIComponents.create_metric_card(
                "Available Rooms",
                available_rooms
            )

        # Charts section
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("### Patient Demographics")
            show_patient_demographics()

        with chart_col2:
            st.markdown("### Department Distribution")
            show_department_distribution()

        # Recent Activities Section
        st.markdown("### Recent Activities")
        tab1, tab2, tab3 = st.tabs([
            "Recent Appointments",
            "Recent Admissions",
            "Room Status"
        ])

        with tab1:
            show_recent_appointments()
        with tab2:
            show_recent_admissions()
        with tab3:
            show_room_status()


# Patient Management Functions
def show_patient_directory():
    """Enhanced patient directory with advanced search and filtering"""
    st.subheader("Patient Directory")

    # Search and Filter Section
    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Search Patients", placeholder="Name, Email, or Phone")
    with col2:
        gender_filter = st.selectbox(
            "Filter by Gender",
            ["All"] + DatabaseConnection.run_query(
                "SELECT Name FROM Gender"
            )['Name'].tolist()
        )
    with col3:
        age_range = st.slider(
            "Age Range",
            0, 100, (0, 100)
        )

    # Construct the query based on filters
    query = """
        SELECT 
            p.PatientID,
            p.FirstName + ' ' + p.LastName AS PatientName,
            g.Name AS Gender,
            DATEDIFF(YEAR, p.DateOfBirth, GETDATE()) AS Age,
            p.ContactNumber,
            p.Email,
            p.Address,
            p.CreatedDate,
            (SELECT COUNT(*) FROM Appointment WHERE PatientID = p.PatientID) AS TotalAppointments,
            (SELECT COUNT(*) FROM Admission WHERE PatientID = p.PatientID) AS TotalAdmissions
        FROM Patient p
        JOIN Gender g ON p.GenderID = g.GenderID
        WHERE 1=1
    """

    params = []

    if search_term:
        query += """
            AND (
                p.FirstName + ' ' + p.LastName LIKE ?
                OR p.Email LIKE ?
                OR p.ContactNumber LIKE ?
            )
        """
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if gender_filter != "All":
        query += " AND g.Name = ?"
        params.append(gender_filter)

    query += """ AND DATEDIFF(YEAR, p.DateOfBirth, GETDATE()) BETWEEN ? AND ?"""
    params.extend([age_range[0], age_range[1]])

    patients = DatabaseConnection.run_query(query, tuple(params))

    if not patients.empty:
        # Add action buttons
        edit_col, view_col = st.columns([1, 1])
        with edit_col:
            if st.button("✏️ Edit Selected Patient"):
                if 'selected_patient' in st.session_state:
                    edit_patient(st.session_state.selected_patient)
        with view_col:
            if st.button("👁️ View Patient History"):
                if 'selected_patient' in st.session_state:
                    view_patient_history(st.session_state.selected_patient)

        # Display paginated results
        page_size = 10
        page_number = st.number_input("Page", min_value=1,
                                      max_value=(len(patients) // page_size) + 1,
                                      value=1)
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size

        # Display patient data with enhanced formatting
        for _, patient in patients[start_idx:end_idx].iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="patient-card">
                            <h4>{patient['PatientName']}</h4>
                            <p>ID: {patient['PatientID']}</p>
                            <p>Age: {patient['Age']} | Gender: {patient['Gender']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="contact-info">
                            <p>📞 {patient['ContactNumber']}</p>
                            <p>📧 {patient['Email']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                        <div class="stats">
                            <p>Appointments: {patient['TotalAppointments']}</p>
                            <p>Admissions: {patient['TotalAdmissions']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col4:
                    if st.button("Select", key=f"select_{patient['PatientID']}"):
                        st.session_state.selected_patient = patient['PatientID']
                st.markdown("---")
    else:
        st.info("No patients found matching the criteria.")


def show_add_patient_form():
    """Form to add new patient"""
    st.subheader("Add New Patient")

    with st.form("add_patient_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name*")
            last_name = st.text_input("Last Name*")

            gender_data = DatabaseConnection.run_query("SELECT GenderID, Name FROM Gender")
            gender = st.selectbox("Gender*", gender_data['Name'].tolist())

            dob = st.date_input("Date of Birth*",
                                max_value=datetime.now(),
                                value=datetime.now() - timedelta(days=365 * 30))

        with col2:
            contact = st.text_input("Contact Number*", placeholder="+1234567890")
            email = st.text_input("Email", placeholder="example@email.com")
            address = st.text_area("Address")

        submit = st.form_submit_button("Add Patient")

        if submit:
            if not (first_name and last_name and contact and dob):
                st.error("Please fill in all required fields (*)")
                return

            if not Validator.validate_phone(contact):
                st.error("Please enter a valid phone number")
                return

            if email and not Validator.validate_email(email):
                st.error("Please enter a valid email address")
                return

            try:
                gender_id = int(gender_data[gender_data['Name'] == gender]['GenderID'].iloc[0])
                dob_str = dob.strftime('%Y-%m-%d')  # Convert date to string

                # Use formatted query instead of parameters for date
                query = f"""
                    INSERT INTO Patient (FirstName, LastName, GenderID, DateOfBirth, 
                                      ContactNumber, Email, Address)
                    VALUES ('{first_name}', '{last_name}', {gender_id}, '{dob_str}', 
                           '{contact}', '{email}', '{address}')
                """

                success = DatabaseConnection.execute_query(query)

                if success:
                    st.success("Patient added successfully!")
                    time.sleep(1)
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"Error adding patient: {str(e)}")


def edit_patient(patient_id: int):
    """Edit existing patient details"""
    patient_data = DatabaseConnection.run_query("""
        SELECT * FROM Patient WHERE PatientID = ?
    """, (patient_id,))

    if not patient_data.empty:
        st.subheader(f"Edit Patient: {patient_data.iloc[0]['FirstName']} {patient_data.iloc[0]['LastName']}")

        with st.form("edit_patient_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name*", value=patient_data.iloc[0]['FirstName'])
                last_name = st.text_input("Last Name*", value=patient_data.iloc[0]['LastName'])

                gender_data = DatabaseConnection.run_query("SELECT GenderID, Name FROM Gender")
                current_gender = gender_data[
                    gender_data['GenderID'] == patient_data.iloc[0]['GenderID']
                    ]['Name'].iloc[0]
                gender = st.selectbox("Gender*", gender_data['Name'].tolist(),
                                      index=gender_data['Name'].tolist().index(current_gender))

                dob = st.date_input("Date of Birth*",
                                    value=patient_data.iloc[0]['DateOfBirth'])

            with col2:
                contact = st.text_input("Contact Number*", value=patient_data.iloc[0]['ContactNumber'])
                email = st.text_input("Email", value=patient_data.iloc[0]['Email'])
                address = st.text_area("Address", value=patient_data.iloc[0]['Address'])

            submit = st.form_submit_button("Update Patient")

            if submit:
                try:
                    gender_id = int(gender_data[gender_data['Name'] == gender]['GenderID'].iloc[0])

                    success = DatabaseConnection.execute_query("""
                        UPDATE Patient 
                        SET FirstName = ?, LastName = ?, GenderID = ?, 
                            DateOfBirth = ?, ContactNumber = ?, Email = ?, Address = ?
                        WHERE PatientID = ?
                    """, (first_name, last_name, gender_id, dob, contact,
                          email, address, patient_id))

                    if success:
                        st.success("Patient updated successfully!")
                        time.sleep(1)
                        st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error updating patient: {str(e)}")


def view_patient_history(patient_id: int):
    """View patient's medical history"""
    patient_data = DatabaseConnection.run_query("""
        SELECT FirstName + ' ' + LastName as PatientName,
               DateOfBirth,
               DATEDIFF(YEAR, DateOfBirth, GETDATE()) as Age
        FROM Patient 
        WHERE PatientID = ?
    """, (patient_id,))

    if not patient_data.empty:
        st.subheader(f"Medical History: {patient_data.iloc[0]['PatientName']}")
        st.markdown(f"**Age:** {patient_data.iloc[0]['Age']} years")

        tab1, tab2 = st.tabs(["Appointments", "Admissions"])

        with tab1:
            appointments = DatabaseConnection.run_query("""
                SELECT 
                    AppointmentDate,
                    DoctorName,
                    Status
                FROM vw_AppointmentDetails
                WHERE PatientID = ?
                ORDER BY AppointmentDate DESC
            """, (patient_id,))

            if not appointments.empty:
                for _, appt in appointments.iterrows():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Doctor:** {appt['DoctorName']}")
                        st.write(f"**Date:** {appt['AppointmentDate'].strftime('%Y-%m-%d %H:%M')}")
                    with col2:
                        status_color = {
                            'Scheduled': 'status-scheduled',
                            'Completed': 'status-completed',
                            'Cancelled': 'status-cancelled'
                        }.get(appt['Status'], '')
                        st.markdown(
                            f"<div class='status-indicator {status_color}'>{appt['Status']}</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown("---")
            else:
                st.info("No appointment history found")

        with tab2:
            admissions = DatabaseConnection.run_query("""
                SELECT 
                    AdmissionDate,
                    DischargeDate,
                    DoctorName,
                    RoomNumber,
                    Status
                FROM vw_AdmissionDetails
                WHERE PatientID = ?
                ORDER BY AdmissionDate DESC
            """, (patient_id,))

            if not admissions.empty:
                for _, adm in admissions.iterrows():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Doctor:** {adm['DoctorName']}")
                        st.write(f"**Room:** {adm['RoomNumber']}")
                        st.write(f"**Admitted:** {adm['AdmissionDate'].strftime('%Y-%m-%d')}")
                        if adm['DischargeDate']:
                            st.write(f"**Discharged:** {adm['DischargeDate'].strftime('%Y-%m-%d')}")
                    with col2:
                        st.markdown(f"**Status:** {adm['Status']}")
                    st.markdown("---")
            else:
                st.info("No admission history found")


def show_patient_analytics():
    """Enhanced analytics dashboard for patient data"""
    st.subheader("Patient Analytics")

    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs(["Demographics", "Visit Patterns", "Health Metrics"])

    with tab1:
        show_demographics_analysis()
    with tab2:
        show_visit_patterns()
    with tab3:
        show_health_metrics()


def show_demographics_analysis():
    """Display detailed demographics analysis"""
    col1, col2 = st.columns(2)

    with col1:
        # Age distribution chart
        age_data = DatabaseConnection.run_query("""
            SELECT 
                CASE 
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 18 THEN '0-17'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 30 THEN '18-29'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 50 THEN '30-49'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 70 THEN '50-69'
                    ELSE '70+'
                END as AgeGroup,
                COUNT(*) as Count
            FROM Patient
            GROUP BY 
                CASE 
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 18 THEN '0-17'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 30 THEN '18-29'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 50 THEN '30-49'
                    WHEN DATEDIFF(YEAR, DateOfBirth, GETDATE()) < 70 THEN '50-69'
                    ELSE '70+'
                END
            ORDER BY AgeGroup
        """)

        if not age_data.empty:
            fig = px.bar(age_data, x='AgeGroup', y='Count',
                         title='Patient Age Distribution',
                         labels={'AgeGroup': 'Age Group', 'Count': 'Number of Patients'})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gender distribution pie chart
        gender_data = DatabaseConnection.run_query("""
            SELECT g.Name as Gender, COUNT(*) as Count
            FROM Patient p
            JOIN Gender g ON p.GenderID = g.GenderID
            GROUP BY g.Name
        """)

        if not gender_data.empty:
            fig = px.pie(gender_data, values='Count', names='Gender',
                         title='Gender Distribution')
            st.plotly_chart(fig, use_container_width=True)


def show_visit_patterns():
    """Display visit pattern analysis"""
    # Monthly visit trends
    visit_data = DatabaseConnection.run_query("""
        SELECT 
            FORMAT(AppointmentDate, 'yyyy-MM') as Month,
            COUNT(*) as VisitCount
        FROM Appointment
        WHERE AppointmentDate >= DATEADD(MONTH, -12, GETDATE())
        GROUP BY FORMAT(AppointmentDate, 'yyyy-MM')
        ORDER BY Month
    """)

    if not visit_data.empty:
        fig = px.line(visit_data, x='Month', y='VisitCount',
                      title='Monthly Visit Trends (Last 12 Months)',
                      labels={'Month': 'Month', 'VisitCount': 'Number of Visits'})
        st.plotly_chart(fig, use_container_width=True)


def show_health_metrics():
    """Display health-related metrics"""
    # Admission duration analysis
    admission_data = DatabaseConnection.run_query("""
        SELECT 
            p.PatientID,
            p.FirstName + ' ' + p.LastName as PatientName,
            COUNT(a.AdmissionID) as AdmissionCount,
            AVG(DATEDIFF(DAY, a.AdmissionDate, 
                COALESCE(a.DischargeDate, GETDATE()))) as AvgStayDuration
        FROM Patient p
        LEFT JOIN Admission a ON p.PatientID = a.PatientID
        GROUP BY p.PatientID, p.FirstName + ' ' + p.LastName
        HAVING COUNT(a.AdmissionID) > 0
        ORDER BY AvgStayDuration DESC
    """)

    if not admission_data.empty:
        fig = px.scatter(admission_data, x='AdmissionCount', y='AvgStayDuration',
                         hover_data=['PatientName'],
                         title='Admission Patterns',
                         labels={'AdmissionCount': 'Number of Admissions',
                                 'AvgStayDuration': 'Average Stay Duration (Days)'})
        st.plotly_chart(fig, use_container_width=True)


def show_patients():
    st.title("Patient Management")

    tab1, tab2, tab3 = st.tabs(["Patient Directory", "Add New Patient", "Patient Analytics"])

    with tab1:
        show_patient_directory()
    with tab2:
        show_add_patient_form()
    with tab3:
        show_patient_analytics()



# Doctors Management Functions
def show_doctor_directory():
    """Enhanced doctor directory with search and filtering"""
    st.subheader("Doctor Directory")

    # Search and Filter Section
    col1, col2 = st.columns(2)

    with col1:
        search_term = st.text_input("Search Doctors",
                                    placeholder="Name, Specialization, or Department")
    with col2:
        department_filter = st.selectbox(
            "Filter by Department",
            ["All"] + DatabaseConnection.run_query(
                "SELECT Name FROM Department"
            )['Name'].tolist()
        )

    # Construct the query based on filters
    query = """
        SELECT 
            d.DoctorID,
            d.FirstName + ' ' + d.LastName AS DoctorName,
            g.Name AS Gender,
            dept.Name AS Department,
            d.Specialization,
            d.ContactNumber,
            d.Email,
            (SELECT COUNT(*) FROM Appointment WHERE DoctorID = d.DoctorID) AS TotalAppointments,
            (SELECT COUNT(*) FROM Admission WHERE DoctorID = d.DoctorID) AS TotalPatients
        FROM Doctor d
        JOIN Gender g ON d.GenderID = g.GenderID
        JOIN Department dept ON d.DepartmentID = dept.DepartmentID
        WHERE 1=1
    """

    params = []

    if search_term:
        query += """
            AND (
                d.FirstName + ' ' + d.LastName LIKE ?
                OR d.Specialization LIKE ?
                OR dept.Name LIKE ?
            )
        """
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    if department_filter != "All":
        query += " AND dept.Name = ?"
        params.append(department_filter)

    doctors = DatabaseConnection.run_query(query, tuple(params))

    if not doctors.empty:
        # Add action buttons
        edit_col, view_col = st.columns([1, 1])
        with edit_col:
            if st.button("✏️ Edit Selected Doctor"):
                if 'selected_doctor' in st.session_state:
                    edit_doctor(st.session_state.selected_doctor)
        with view_col:
            if st.button("👁️ View Doctor Schedule"):
                if 'selected_doctor' in st.session_state:
                    view_doctor_schedule(st.session_state.selected_doctor)

        # Display doctor data with enhanced formatting
        for _, doctor in doctors.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="doctor-card">
                            <h4>{doctor['DoctorName']}</h4>
                            <p>Specialization: {doctor['Specialization']}</p>
                            <p>Department: {doctor['Department']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="contact-info">
                            <p>📞 {doctor['ContactNumber']}</p>
                            <p>📧 {doctor['Email']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                        <div class="stats">
                            <p>Total Appointments: {doctor['TotalAppointments']}</p>
                            <p>Total Patients: {doctor['TotalPatients']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col4:
                    if st.button("Select", key=f"select_{doctor['DoctorID']}"):
                        st.session_state.selected_doctor = doctor['DoctorID']
                st.markdown("---")
    else:
        st.info("No doctors found matching the criteria.")


def show_add_doctor_form():
    """Form to add new doctor"""
    st.subheader("Add New Doctor")

    with st.form("add_doctor_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name*")
            last_name = st.text_input("Last Name*")

            gender_data = DatabaseConnection.run_query("SELECT GenderID, Name FROM Gender")
            gender = st.selectbox("Gender*", gender_data['Name'].tolist())

            department_data = DatabaseConnection.run_query("SELECT DepartmentID, Name FROM Department")
            department = st.selectbox("Department*", department_data['Name'].tolist())

        with col2:
            specialization = st.text_input("Specialization*")
            contact = st.text_input("Contact Number*", placeholder="+1234567890")
            email = st.text_input("Email", placeholder="doctor@hospital.com")

        submit = st.form_submit_button("Add Doctor")

        if submit:
            if not (first_name and last_name and specialization and contact):
                st.error("Please fill in all required fields (*)")
                return

            if not Validator.validate_phone(contact):
                st.error("Please enter a valid phone number")
                return

            if email and not Validator.validate_email(email):
                st.error("Please enter a valid email address")
                return

            try:
                gender_id = int(gender_data[gender_data['Name'] == gender]['GenderID'].iloc[0])
                dept_id = int(department_data[department_data['Name'] == department]['DepartmentID'].iloc[0])

                success = DatabaseConnection.execute_query("""
                    INSERT INTO Doctor (FirstName, LastName, GenderID, DepartmentID, 
                                     Specialization, ContactNumber, Email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (first_name, last_name, gender_id, dept_id,
                      specialization, contact, email))

                if success:
                    st.success("Doctor added successfully!")
                    time.sleep(1)
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"Error adding doctor: {str(e)}")


def edit_doctor(doctor_id: int):
    """Edit existing doctor details"""
    doctor_data = DatabaseConnection.run_query("""
        SELECT * FROM Doctor WHERE DoctorID = ?
    """, (doctor_id,))

    if not doctor_data.empty:
        st.subheader(f"Edit Doctor: {doctor_data.iloc[0]['FirstName']} {doctor_data.iloc[0]['LastName']}")

        with st.form("edit_doctor_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name*", value=doctor_data.iloc[0]['FirstName'])
                last_name = st.text_input("Last Name*", value=doctor_data.iloc[0]['LastName'])

                gender_data = DatabaseConnection.run_query("SELECT GenderID, Name FROM Gender")
                current_gender = gender_data[
                    gender_data['GenderID'] == doctor_data.iloc[0]['GenderID']
                    ]['Name'].iloc[0]
                gender = st.selectbox("Gender*", gender_data['Name'].tolist(),
                                      index=gender_data['Name'].tolist().index(current_gender))

                department_data = DatabaseConnection.run_query("SELECT DepartmentID, Name FROM Department")
                current_dept = department_data[
                    department_data['DepartmentID'] == doctor_data.iloc[0]['DepartmentID']
                    ]['Name'].iloc[0]
                department = st.selectbox("Department*", department_data['Name'].tolist(),
                                          index=department_data['Name'].tolist().index(current_dept))

            with col2:
                specialization = st.text_input("Specialization*",
                                               value=doctor_data.iloc[0]['Specialization'])
                contact = st.text_input("Contact Number*",
                                        value=doctor_data.iloc[0]['ContactNumber'])
                email = st.text_input("Email", value=doctor_data.iloc[0]['Email'])

            submit = st.form_submit_button("Update Doctor")

            if submit:
                try:
                    gender_id = int(gender_data[gender_data['Name'] == gender]['GenderID'].iloc[0])
                    dept_id = int(department_data[department_data['Name'] == department]['DepartmentID'].iloc[0])

                    success = DatabaseConnection.execute_query("""
                        UPDATE Doctor 
                        SET FirstName = ?, LastName = ?, GenderID = ?, DepartmentID = ?,
                            Specialization = ?, ContactNumber = ?, Email = ?
                        WHERE DoctorID = ?
                    """, (first_name, last_name, gender_id, dept_id, specialization,
                          contact, email, doctor_id))

                    if success:
                        st.success("Doctor updated successfully!")
                        time.sleep(1)
                        st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error updating doctor: {str(e)}")


def view_doctor_schedule(doctor_id: int):
    """View doctor's schedule and appointments"""
    doctor_data = DatabaseConnection.run_query("""
        SELECT 
            FirstName + ' ' + LastName as DoctorName,
            Specialization,
            dept.Name as Department
        FROM Doctor d
        JOIN Department dept ON d.DepartmentID = dept.DepartmentID
        WHERE DoctorID = ?
    """, (doctor_id,))

    if not doctor_data.empty:
        st.subheader(f"Schedule: Dr. {doctor_data.iloc[0]['DoctorName']}")
        st.markdown(f"**Specialization:** {doctor_data.iloc[0]['Specialization']}")
        st.markdown(f"**Department:** {doctor_data.iloc[0]['Department']}")

        # Date filter for schedule
        selected_date = st.date_input("Select Date", datetime.now())

        # Get appointments for selected date
        appointments = DatabaseConnection.run_query("""
            SELECT 
                a.AppointmentID,
                p.FirstName + ' ' + p.LastName as PatientName,
                a.AppointmentDate,
                a.Status
            FROM Appointment a
            JOIN Patient p ON a.PatientID = p.PatientID
            WHERE a.DoctorID = ?
            AND CAST(a.AppointmentDate as DATE) = CAST(? as DATE)
            ORDER BY a.AppointmentDate
        """, (doctor_id, selected_date))

        if not appointments.empty:
            st.subheader("Appointments")
            for _, appt in appointments.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Patient:** {appt['PatientName']}")
                        st.write(f"**Time:** {appt['AppointmentDate'].strftime('%H:%M')}")
                    with col2:
                        status_color = {
                            'Scheduled': 'status-scheduled',
                            'Completed': 'status-completed',
                            'Cancelled': 'status-cancelled'
                        }.get(appt['Status'], '')
                        st.markdown(
                            f"<div class='status-indicator {status_color}'>{appt['Status']}</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown("---")
        else:
            st.info("No appointments scheduled for this date")

        # Show statistics
        col1, col2 = st.columns(2)
        with col1:
            total_appointments = DatabaseConnection.run_query("""
                SELECT COUNT(*) as count
                FROM Appointment
                WHERE DoctorID = ?
                AND MONTH(AppointmentDate) = MONTH(GETDATE())
                AND YEAR(AppointmentDate) = YEAR(GETDATE())
            """, (doctor_id,)).iloc[0]['count']

            st.metric("This Month's Appointments", total_appointments)

        with col2:
            completion_rate = DatabaseConnection.run_query("""
                SELECT 
                    CAST(SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) AS FLOAT) /
                    COUNT(*) * 100 as completion_rate
                FROM Appointment
                WHERE DoctorID = ?
                AND MONTH(AppointmentDate) = MONTH(GETDATE())
                AND YEAR(AppointmentDate) = YEAR(GETDATE())
            """, (doctor_id,)).iloc[0]['completion_rate']

            st.metric("Completion Rate", f"{completion_rate:.1f}%")


def show_doctors():
    """Main doctors page"""
    st.title("Doctor Management")

    tabs = st.tabs(["Doctor Directory", "Add New Doctor", "Department Analytics"])

    with tabs[0]:
        show_doctor_directory()
    with tabs[1]:
        show_add_doctor_form()
    with tabs[2]:
        show_department_analytics()


def show_department_analytics():
    """Show department-wise analytics"""
    st.subheader("Department Analytics")

    # Get department statistics
    dept_stats = DatabaseConnection.run_query("""
        SELECT 
            d.Name as Department,
            COUNT(DISTINCT doc.DoctorID) as DoctorCount,
            COUNT(DISTINCT a.PatientID) as PatientCount,
            COUNT(DISTINCT apt.AppointmentID) as AppointmentCount
        FROM Department d
        LEFT JOIN Doctor doc ON d.DepartmentID = doc.DepartmentID
        LEFT JOIN Appointment apt ON doc.DoctorID = apt.DoctorID
        LEFT JOIN Admission a ON doc.DoctorID = a.DoctorID
        GROUP BY d.Name
    """)

    if not dept_stats.empty:
        # Create visualization
        fig = go.Figure()

        # Add bars for doctor count
        fig.add_trace(go.Bar(
            name='Doctors',
            x=dept_stats['Department'],
            y=dept_stats['DoctorCount'],
            marker_color='#2E86C1'
        ))

        # Add bars for patient count
        fig.add_trace(go.Bar(
            name='Patients',
            x=dept_stats['Department'],
            y=dept_stats['PatientCount'],
            marker_color='#1ABC9C'
        ))

        # Add line for appointments
        fig.add_trace(go.Scatter(
            name='Appointments',
            x=dept_stats['Department'],
            y=dept_stats['AppointmentCount'],
            mode='lines+markers',
            line=dict(color='#E74C3C', width=2),
            yaxis='y2'
        ))

        # Update layout
        fig.update_layout(
            title='Department Statistics Overview',
            barmode='group',
            yaxis=dict(title='Count'),
            yaxis2=dict(
                title='Appointments',
                overlaying='y',
                side='right'
            ),
            height=500,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display detailed statistics
        st.subheader("Detailed Department Statistics")

        for _, dept in dept_stats.iterrows():
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Doctors", dept['DoctorCount'])
                with col2:
                    st.metric("Patients", dept['PatientCount'])
                with col3:
                    st.metric("Appointments", dept['AppointmentCount'])

                # Get department workload distribution
                workload = DatabaseConnection.run_query("""
                            SELECT 
                                doc.FirstName + ' ' + doc.LastName as DoctorName,
                                COUNT(a.AppointmentID) as AppointmentCount
                            FROM Doctor doc
                            LEFT JOIN Appointment a ON doc.DoctorID = a.DoctorID
                            JOIN Department d ON doc.DepartmentID = d.DepartmentID
                            WHERE d.Name = ?
                            GROUP BY doc.FirstName, doc.LastName
                        """, (dept['Department'],))

                if not workload.empty:
                    # Create workload distribution chart
                    fig_workload = px.bar(
                        workload,
                        x='DoctorName',
                        y='AppointmentCount',
                        title=f"Workload Distribution - {dept['Department']}",
                        labels={
                            'DoctorName': 'Doctor',
                            'AppointmentCount': 'Number of Appointments'
                        }
                    )
                    st.plotly_chart(fig_workload, use_container_width=True)

                st.markdown("---")
    else:
        st.info("No department statistics available")

    def calculate_doctor_metrics():
        """Calculate key performance metrics for doctors"""
        return DatabaseConnection.run_query("""
                SELECT 
                    d.DoctorID,
                    d.FirstName + ' ' + d.LastName as DoctorName,
                    COUNT(DISTINCT a.AppointmentID) as TotalAppointments,
                    COUNT(DISTINCT CASE WHEN a.Status = 'Completed' THEN a.AppointmentID END) as CompletedAppointments,
                    COUNT(DISTINCT p.PatientID) as UniquePatients,
                    AVG(CAST(
                        CASE WHEN a.Status = 'Completed' THEN 1 ELSE 0 END
                    as FLOAT)) * 100 as CompletionRate
                FROM Doctor d
                LEFT JOIN Appointment a ON d.DoctorID = a.DoctorID
                LEFT JOIN Patient p ON a.PatientID = p.PatientID
                GROUP BY d.DoctorID, d.FirstName, d.LastName
            """)

    def show_doctor_availability(doctor_id: int):
        """Show doctor's availability calendar"""
        appointments = DatabaseConnection.run_query("""
                SELECT 
                    AppointmentDate,
                    Status
                FROM Appointment
                WHERE DoctorID = ?
                AND AppointmentDate >= GETDATE()
                ORDER BY AppointmentDate
            """, (doctor_id,))

        # Convert to calendar view
        if not appointments.empty:
            calendar_data = {}
            for _, appt in appointments.iterrows():
                date = appt['AppointmentDate'].strftime('%Y-%m-%d')
                if date not in calendar_data:
                    calendar_data[date] = []
                calendar_data[date].append({
                    'time': appt['AppointmentDate'].strftime('%H:%M'),
                    'status': appt['Status']
                })

            # Display calendar
            selected_date = st.date_input("Select Date")
            selected_date_str = selected_date.strftime('%Y-%m-%d')

            if selected_date_str in calendar_data:
                st.write("Appointments for", selected_date_str)
                for appt in calendar_data[selected_date_str]:
                    st.markdown(f"""
                            <div class="appointment-slot">
                                <span>{appt['time']}</span>
                                <span class="status-{appt['status'].lower()}">{appt['status']}</span>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No appointments scheduled for this date")
        else:
            st.info("No upcoming appointments")

    def show_doctor_performance(doctor_id: int):
        """Show doctor's performance metrics"""
        metrics = DatabaseConnection.run_query("""
                SELECT 
                    COUNT(DISTINCT a.AppointmentID) as TotalAppointments,
                    COUNT(DISTINCT CASE WHEN a.Status = 'Completed' THEN a.AppointmentID END) as CompletedAppointments,
                    COUNT(DISTINCT p.PatientID) as UniquePatients,
                    AVG(CAST(
                        CASE WHEN a.Status = 'Completed' THEN 1 ELSE 0 END
                    as FLOAT)) * 100 as CompletionRate
                FROM Doctor d
                LEFT JOIN Appointment a ON d.DoctorID = a.DoctorID
                LEFT JOIN Patient p ON a.PatientID = p.PatientID
                WHERE d.DoctorID = ?
                GROUP BY d.DoctorID
            """, (doctor_id,))

        if not metrics.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Appointments", metrics.iloc[0]['TotalAppointments'])
            with col2:
                st.metric("Completed Appointments", metrics.iloc[0]['CompletedAppointments'])
            with col3:
                st.metric("Unique Patients", metrics.iloc[0]['UniquePatients'])
            with col4:
                st.metric("Completion Rate", f"{metrics.iloc[0]['CompletionRate']:.1f}%")


# Appointment Management Functions
def show_appointments():
    """Main appointments page"""
    st.title("Appointment Management")

    tabs = st.tabs(["Appointments Calendar", "Schedule Appointment", "Appointment Analytics"])

    with tabs[0]:
        show_appointments_calendar()
    with tabs[1]:
        schedule_appointment()
    with tabs[2]:
        show_appointment_analytics()


def show_appointments_calendar():
    """Display appointments in calendar view"""
    st.subheader("Appointments Calendar")

    # Date filter
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_date = st.date_input("Select Date",
                                      datetime.now(),
                                      key="calendar_date_select")
    with col2:
        view_type = st.selectbox("View", ["Day", "Week", "Month"],
                                 key="calendar_view_type")

    # Filter options
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        doctors = DatabaseConnection.run_query("""
            SELECT FirstName + ' ' + LastName as DoctorName 
            FROM Doctor
            ORDER BY LastName, FirstName
        """)
        doctor_list = ["All"] + doctors['DoctorName'].tolist() if not doctors.empty else ["All"]
        doctor_filter = st.selectbox("Filter by Doctor", doctor_list, key="doctor_filter")

    with filter_col2:
        status_filter = st.selectbox("Filter by Status",
                                     ["All", "Scheduled", "Completed", "Cancelled"],
                                     key="status_filter")

    # Calculate date range based on view type
    start_date = selected_date
    if view_type == "Day":
        end_date = start_date
    elif view_type == "Week":
        end_date = start_date + timedelta(days=6)
    else:  # Month
        next_month = selected_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)

    # Convert dates to strings for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Construct query
    query = f"""
        SELECT 
            a.AppointmentID,
            p.FirstName + ' ' + p.LastName as PatientName,
            d.FirstName + ' ' + d.LastName as DoctorName,
            a.AppointmentDate,
            a.Status
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        WHERE CAST(a.AppointmentDate as DATE) BETWEEN '{start_date_str}' AND '{end_date_str}'
    """

    if doctor_filter != "All":
        query += f" AND d.FirstName + ' ' + d.LastName = '{doctor_filter}'"

    if status_filter != "All":
        query += f" AND a.Status = '{status_filter}'"

    query += " ORDER BY a.AppointmentDate"

    appointments = DatabaseConnection.run_query(query)

    if not appointments.empty:
        # Create date range for selected view
        date_range = pd.date_range(start=start_date, end=end_date)

        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            day_appointments = appointments[
                appointments['AppointmentDate'].dt.strftime('%Y-%m-%d') == date_str
                ]

            if not day_appointments.empty:
                st.markdown(f"### {date.strftime('%A, %B %d, %Y')}")

                for _, appt in day_appointments.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.markdown(f"""
                                <div class="appointment-info">
                                    <p><strong>Patient:</strong> {appt['PatientName']}</p>
                                    <p><strong>Doctor:</strong> {appt['DoctorName']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                                <div class="appointment-time">
                                    <p><strong>Time:</strong> {appt['AppointmentDate'].strftime('%H:%M')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with col3:
                            status_color = {
                                'Scheduled': 'status-scheduled',
                                'Completed': 'status-completed',
                                'Cancelled': 'status-cancelled'
                            }.get(appt['Status'], '')

                            if st.button("Update", key=f"update_{appt['AppointmentID']}"):
                                update_appointment_status(appt['AppointmentID'])

                            st.markdown(f"""
                                <div class="status-indicator {status_color}">
                                    {appt['Status']}
                                </div>
                            """, unsafe_allow_html=True)
                        st.markdown("---")
    else:
        st.info("No appointments found for the selected period")


def schedule_appointment():
    """Form to schedule new appointments"""
    st.subheader("Schedule New Appointment")

    with st.form("schedule_appointment_form"):
        # Patient selection with search
        patient_search = st.text_input("Search Patient",
                                       placeholder="Enter patient name",
                                       key="patient_search_input")

        patients = DatabaseConnection.run_query("""
            SELECT PatientID, FirstName + ' ' + LastName as PatientName
            FROM Patient
            WHERE FirstName + ' ' + LastName LIKE ?
            ORDER BY LastName, FirstName
        """, (f"%{patient_search}%" if patient_search else "%",))

        if not patients.empty:
            selected_patient = st.selectbox("Select Patient",
                                            patients['PatientName'].tolist(),
                                            key="patient_select")

            # Doctor selection with department filter
            col1, col2 = st.columns(2)
            with col1:
                departments = DatabaseConnection.run_query("SELECT DepartmentID, Name FROM Department")
                selected_dept = st.selectbox("Select Department",
                                             departments['Name'].tolist(),
                                             key="dept_select")

            with col2:
                doctors = DatabaseConnection.run_query("""
                    SELECT d.DoctorID, d.FirstName + ' ' + d.LastName as DoctorName
                    FROM Doctor d
                    JOIN Department dept ON d.DepartmentID = dept.DepartmentID
                    WHERE dept.Name = ?
                    ORDER BY d.LastName, d.FirstName
                """, (selected_dept,))

                if not doctors.empty:
                    selected_doctor = st.selectbox("Select Doctor",
                                                   doctors['DoctorName'].tolist(),
                                                   key="doctor_select")

                    # Date and time selection
                    date_col, time_col = st.columns(2)
                    with date_col:
                        appointment_date = st.date_input(
                            "Appointment Date",
                            min_value=datetime.now().date(),
                            value=datetime.now().date() + timedelta(days=1),
                            key="appointment_date"
                        )
                    with time_col:
                        appointment_time = st.time_input(
                            "Appointment Time",
                            value=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0).time(),
                            key="appointment_time"
                        )

                    if st.form_submit_button("Schedule Appointment"):
                        try:
                            # Get IDs
                            patient_id = int(patients[patients['PatientName'] == selected_patient]['PatientID'].iloc[0])
                            doctor_id = int(doctors[doctors['DoctorName'] == selected_doctor]['DoctorID'].iloc[0])

                            # Combine date and time
                            appointment_datetime = datetime.combine(appointment_date, appointment_time)

                            # Check for conflicts
                            conflicts = DatabaseConnection.run_query(f"""
                                SELECT AppointmentID
                                FROM Appointment
                                WHERE DoctorID = {doctor_id}
                                AND CAST(AppointmentDate AS DATE) = '{appointment_date}'
                                AND DATEPART(HOUR, AppointmentDate) = {appointment_time.hour}
                                AND Status != 'Cancelled'
                            """)

                            if not conflicts.empty:
                                st.error("This time slot is already booked. Please select another time.")
                                return

                            # Schedule appointment
                            success = DatabaseConnection.execute_query("""
                                INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, Status)
                                VALUES (?, ?, ?, 'Scheduled')
                            """, (patient_id, doctor_id, appointment_datetime))

                            if success:
                                st.success("Appointment scheduled successfully!")
                                time.sleep(1)
                                st.experimental_rerun()

                        except Exception as e:
                            st.error(f"Error scheduling appointment: {str(e)}")
                else:
                    st.error("No doctors available in selected department")
        else:
            st.info("No patients found matching the search criteria")


def update_appointment_status(appointment_id: int):
    """Update appointment status"""
    appointment = DatabaseConnection.run_query("""
        SELECT 
            a.AppointmentID,
            p.FirstName + ' ' + p.LastName as PatientName,
            d.FirstName + ' ' + d.LastName as DoctorName,
            a.AppointmentDate,
            a.Status
        FROM Appointment a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        WHERE a.AppointmentID = ?
    """, (appointment_id,))

    if not appointment.empty:
        with st.form(f"update_status_form_{appointment_id}"):
            st.write(f"**Patient:** {appointment.iloc[0]['PatientName']}")
            st.write(f"**Doctor:** {appointment.iloc[0]['DoctorName']}")
            st.write(f"**Date:** {appointment.iloc[0]['AppointmentDate'].strftime('%Y-%m-%d %H:%M')}")

            current_status = appointment.iloc[0]['Status']
            status_options = ["Scheduled", "Completed", "Cancelled"]
            current_index = status_options.index(current_status)

            new_status = st.selectbox(
                "New Status",
                status_options,
                index=current_index,
                key=f"status_select_{appointment_id}"
            )

            if st.form_submit_button("Update Status"):
                success = DatabaseConnection.execute_query(f"""
                    UPDATE Appointment
                    SET Status = '{new_status}'
                    WHERE AppointmentID = {appointment_id}
                """)

                if success:
                    st.success("Appointment status updated successfully!")
                    time.sleep(1)
                    st.experimental_rerun()


def show_appointment_analytics():
    """Display appointment analytics"""
    st.subheader("Appointment Analytics")

    # Time period selection
    period = st.selectbox(
        "Select Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last Year"],
        key="analytics_period"
    )

    # Calculate date range
    end_date = datetime.now()
    if period == "Last 7 Days":
        start_date = end_date - timedelta(days=7)
    elif period == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
    elif period == "Last 3 Months":
        start_date = end_date - timedelta(days=90)
    elif period == "Last 6 Months":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = end_date - timedelta(days=365)

    # Convert dates to strings for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Get appointment statistics
    stats = DatabaseConnection.run_query(f"""
        SELECT 
            COUNT(*) as TotalAppointments,
            SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as CompletedAppointments,
            SUM(CASE WHEN Status = 'Cancelled' THEN 1 ELSE 0 END) as CancelledAppointments,
            COUNT(DISTINCT PatientID) as UniquePatients
        FROM Appointment
        WHERE AppointmentDate BETWEEN '{start_date_str}' AND '{end_date_str}'
    """)

    if not stats.empty:
        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Appointments", stats.iloc[0]['TotalAppointments'])
        with col2:
            completion_rate = (stats.iloc[0]['CompletedAppointments'] /
                               stats.iloc[0]['TotalAppointments'] * 100
                               if stats.iloc[0]['TotalAppointments'] > 0 else 0)
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        with col3:
            cancellation_rate = (stats.iloc[0]['CancelledAppointments'] /
                                 stats.iloc[0]['TotalAppointments'] * 100
                                 if stats.iloc[0]['TotalAppointments'] > 0 else 0)
            st.metric("Cancellation Rate", f"{cancellation_rate:.1f}%")

        # Show trends
        show_appointment_trends(start_date_str, end_date_str)


def show_appointment_trends(start_date: str, end_date: str):
    """Display appointment trends"""
    trends = DatabaseConnection.run_query(f"""
        SELECT 
            CAST(AppointmentDate as DATE) as Date,
            COUNT(*) as AppointmentCount,
            SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as CompletedCount,
            SUM(CASE WHEN Status = 'Cancelled' THEN 1 ELSE 0 END) as CancelledCount
        FROM Appointment
        WHERE AppointmentDate BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY CAST(AppointmentDate as DATE)
        ORDER BY Date
    """)

    if not trends.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=trends['Date'],
            y=trends['CompletedCount'],
            name='Completed',
            mode='lines+markers'
        ))

        fig.add_trace(go.Scatter(
            x=trends['Date'],
            y=trends['CancelledCount'],
            name='Cancelled',
            mode='lines+markers'
        ))

        fig.update_layout(
            title='Daily Appointment Trends',
            xaxis_title='Date',
            yaxis_title='Number of Appointments',
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)


# Admissions Management Functions
def show_admissions():
    """Main admissions page"""
    st.title("Admission Management")

    tabs = st.tabs(["Current Admissions", "New Admission", "Discharge Management", "Admission Analytics"])

    with tabs[0]:
        show_current_admissions()
    with tabs[1]:
        create_new_admission()
    with tabs[2]:
        manage_discharges()
    with tabs[3]:
        show_admission_analytics()


def show_current_admissions():
    """Display current hospital admissions"""
    st.subheader("Current Admissions")

    # Search and filter options
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search Patient",
                                    placeholder="Enter patient name",
                                    key="current_admission_search")
    with col2:
        room_type_filter = st.selectbox(
            "Filter by Room Type",
            ["All", "General", "Private", "ICU"],
            key="room_type_filter"
        )

    # Construct query
    query = """
        SELECT 
            a.AdmissionID,
            p.FirstName + ' ' + p.LastName as PatientName,
            d.FirstName + ' ' + d.LastName as DoctorName,
            r.RoomNumber,
            r.RoomType,
            a.AdmissionDate,
            DATEDIFF(DAY, a.AdmissionDate, GETDATE()) as DaysAdmitted
        FROM Admission a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        JOIN Room r ON a.RoomID = r.RoomID
        WHERE a.Status = 'Admitted'
    """

    params = []
    if search_term:
        query += " AND p.FirstName + ' ' + p.LastName LIKE ?"
        params.append(f"%{search_term}%")

    if room_type_filter != "All":
        query += " AND r.RoomType = ?"
        params.append(room_type_filter)

    query += " ORDER BY a.AdmissionDate DESC"

    admissions = DatabaseConnection.run_query(query, tuple(params) if params else None)

    if not admissions.empty:
        for _, admission in admissions.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"""
                        <div class="admission-info">
                            <h4>{admission['PatientName']}</h4>
                            <p><strong>Doctor:</strong> {admission['DoctorName']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class="room-info">
                            <p><strong>Room:</strong> {admission['RoomNumber']} ({admission['RoomType']})</p>
                            <p><strong>Days Admitted:</strong> {admission['DaysAdmitted']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col3:
                    if st.button("Discharge", key=f"discharge_btn_{admission['AdmissionID']}"):
                        initiate_discharge(admission['AdmissionID'])
                st.markdown("---")
    else:
        st.info("No current admissions found")

def initiate_discharge(admission_id: int):
    """Initiate the discharge process for a patient"""
    admission = DatabaseConnection.run_query("""
        SELECT 
            a.AdmissionID,
            p.FirstName + ' ' + p.LastName as PatientName,
            d.FirstName + ' ' + d.LastName as DoctorName,
            r.RoomNumber,
            a.AdmissionDate,
            r.RoomID
        FROM Admission a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        JOIN Room r ON a.RoomID = r.RoomID
        WHERE a.AdmissionID = ?
    """, (admission_id,))

    if not admission.empty:
        st.subheader("Process Discharge")
        with st.form(f"discharge_form_{admission_id}"):
            st.write(f"**Patient:** {admission.iloc[0]['PatientName']}")
            st.write(f"**Doctor:** {admission.iloc[0]['DoctorName']}")
            st.write(f"**Room:** {admission.iloc[0]['RoomNumber']}")
            st.write(f"**Admission Date:** {admission.iloc[0]['AdmissionDate'].strftime('%Y-%m-%d')}")

            discharge_date = st.date_input(
                "Discharge Date",
                datetime.now(),
                key=f"discharge_date_{admission_id}"
            )
            discharge_notes = st.text_area(
                "Discharge Notes",
                key=f"discharge_notes_{admission_id}"
            )

            if st.form_submit_button("Confirm Discharge"):
                success = process_discharge(
                    admission_id,
                    discharge_date,
                    discharge_notes
                )
                if success:
                    st.success("Patient discharged successfully!")
                    time.sleep(1)
                    st.experimental_rerun()


def create_new_admission():
    """Form to create new patient admission"""
    st.subheader("New Patient Admission")

    with st.form("new_admission_form"):
        # Patient Selection
        patient_search = st.text_input("Search Patient",
                                       placeholder="Enter patient name",
                                       key="new_admission_patient_search")
        patients = DatabaseConnection.run_query("""
            SELECT PatientID, FirstName + ' ' + LastName as PatientName
            FROM Patient
            WHERE FirstName + ' ' + LastName LIKE ?
            ORDER BY LastName, FirstName
        """, (f"%{patient_search}%" if patient_search else "%",))

        if not patients.empty:
            selected_patient = st.selectbox(
                "Select Patient",
                patients['PatientName'].tolist(),
                key="new_admission_patient_select"
            )

            # Doctor Selection
            col1, col2 = st.columns(2)
            with col1:
                departments = DatabaseConnection.run_query("SELECT DepartmentID, Name FROM Department")
                selected_dept = st.selectbox("Department",
                                             departments['Name'].tolist(),
                                             key="new_admission_dept_select")

                doctors = DatabaseConnection.run_query("""
                    SELECT d.DoctorID, d.FirstName + ' ' + d.LastName as DoctorName
                    FROM Doctor d
                    JOIN Department dept ON d.DepartmentID = dept.DepartmentID
                    WHERE dept.Name = ?
                """, (selected_dept,))

                selected_doctor = st.selectbox("Attending Doctor",
                                               doctors['DoctorName'].tolist(),
                                               key="new_admission_doctor_select")

            # Room Selection
            with col2:
                room_type = st.selectbox("Room Type",
                                         ["General", "Private", "ICU"],
                                         key="new_admission_room_type")
                available_rooms = DatabaseConnection.run_query("""
                    SELECT RoomID, RoomNumber
                    FROM Room
                    WHERE RoomType = ? AND Status = 'Available'
                """, (room_type,))

                if not available_rooms.empty:
                    selected_room = st.selectbox(
                        "Available Rooms",
                        available_rooms['RoomNumber'].tolist(),
                        key="new_admission_room_select"
                    )
                else:
                    st.error(f"No {room_type} rooms available")
                    selected_room = None

            # Admission Details
            admission_date = st.date_input("Admission Date",
                                           value=datetime.now(),
                                           key="new_admission_date")
            admission_notes = st.text_area("Admission Notes",
                                           key="new_admission_notes")

            if st.form_submit_button("Admit Patient"):
                if not selected_room:
                    st.error("No available rooms of the selected type")
                    return

                try:
                    # Get IDs from selections
                    patient_id = int(patients[patients['PatientName'] == selected_patient]['PatientID'].iloc[0])
                    doctor_id = int(doctors[doctors['DoctorName'] == selected_doctor]['DoctorID'].iloc[0])
                    room_id = int(available_rooms[available_rooms['RoomNumber'] == selected_room]['RoomID'].iloc[0])

                    # Create admission transaction
                    queries = [
                        ("""
                            INSERT INTO Admission 
                            (PatientID, DoctorID, RoomID, AdmissionDate, Status, Notes)
                            VALUES (?, ?, ?, ?, 'Admitted', ?)
                        """, (patient_id, doctor_id, room_id, admission_date, admission_notes)),
                        ("""
                            UPDATE Room 
                            SET Status = 'Occupied' 
                            WHERE RoomID = ?
                        """, (room_id,))
                    ]

                    success = execute_transaction(queries)
                    if success:
                        st.success("Patient admitted successfully!")
                        time.sleep(1)
                        st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error admitting patient: {str(e)}")
        else:
            st.info("No patients found matching the search criteria")


def manage_discharges():
    """Manage patient discharges"""
    st.subheader("Discharge Management")

    # Get current admissions eligible for discharge
    admissions = DatabaseConnection.run_query("""
        SELECT 
            a.AdmissionID,
            p.FirstName + ' ' + p.LastName as PatientName,
            d.FirstName + ' ' + d.LastName as DoctorName,
            r.RoomNumber,
            r.RoomType,
            a.AdmissionDate,
            DATEDIFF(DAY, a.AdmissionDate, GETDATE()) as DaysAdmitted
        FROM Admission a
        JOIN Patient p ON a.PatientID = p.PatientID
        JOIN Doctor d ON a.DoctorID = d.DoctorID
        JOIN Room r ON a.RoomID = r.RoomID
        WHERE a.Status = 'Admitted'
        ORDER BY a.AdmissionDate
    """)

    if not admissions.empty:
        for _, admission in admissions.iterrows():
            with st.expander(f"Discharge: {admission['PatientName']} - Room {admission['RoomNumber']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Doctor:** {admission['DoctorName']}")
                    st.write(f"**Room Type:** {admission['RoomType']}")
                    st.write(f"**Admitted On:** {admission['AdmissionDate'].strftime('%Y-%m-%d')}")
                    st.write(f"**Days Admitted:** {admission['DaysAdmitted']}")

                with col2:
                    discharge_date = st.date_input(
                        "Discharge Date",
                        value=datetime.now(),
                        key=f"discharge_date_{admission['AdmissionID']}"
                    )
                    discharge_notes = st.text_area(
                        "Discharge Notes",
                        key=f"discharge_notes_{admission['AdmissionID']}"
                    )

                    if st.button("Process Discharge",
                                 key=f"process_discharge_{admission['AdmissionID']}"):
                        process_discharge(
                            admission['AdmissionID'],
                            discharge_date,
                            discharge_notes
                        )
    else:
        st.info("No patients currently admitted")


def process_discharge(admission_id: int, discharge_date: datetime, discharge_notes: str):
    """Process patient discharge"""
    try:
        # Get room ID for the admission
        room_data = DatabaseConnection.run_query("""
            SELECT RoomID
            FROM Admission
            WHERE AdmissionID = ?
        """, (admission_id,))

        if not room_data.empty:
            room_id = int(room_data.iloc[0]['RoomID'])
            discharge_date_str = discharge_date.strftime('%Y-%m-%d')

            # Create discharge transaction with only essential columns
            queries = [
                ("""
                    UPDATE Admission 
                    SET Status = 'Discharged',
                        DischargeDate = CAST(? AS DATE)
                    WHERE AdmissionID = ?
                """, (discharge_date_str, admission_id)),
                ("""
                    UPDATE Room 
                    SET Status = 'Available'
                    WHERE RoomID = ?
                """, (room_id,))
            ]

            success = execute_transaction(queries)
            return success

    except Exception as e:
        st.error(f"Error processing discharge: {str(e)}")
        return False

def show_admission_analytics():
    """Display admission analytics and statistics"""
    st.subheader("Admission Analytics")

    # Time period selection
    period = st.selectbox(
        "Select Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last Year"],
        key="admission_analytics_period"
    )

    # Calculate date range
    end_date = datetime.now()
    if period == "Last 7 Days":
        start_date = end_date - timedelta(days=7)
    elif period == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
    elif period == "Last 3 Months":
        start_date = end_date - timedelta(days=90)
    elif period == "Last 6 Months":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = end_date - timedelta(days=365)

    # Convert dates to strings for query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Get admission statistics
    stats = DatabaseConnection.run_query(f"""
        SELECT 
            COUNT(*) as TotalAdmissions,
            SUM(CASE WHEN Status = 'Discharged' THEN 1 ELSE 0 END) as Discharged,
            COUNT(DISTINCT PatientID) as UniquePatients,
            AVG(DATEDIFF(DAY, AdmissionDate, 
                CASE WHEN DischargeDate IS NOT NULL THEN DischargeDate 
                ELSE GETDATE() END)) as AvgStayDuration
        FROM Admission
        WHERE AdmissionDate BETWEEN '{start_date_str}' AND '{end_date_str}'
    """)

    if not stats.empty:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Admissions", stats.iloc[0]['TotalAdmissions'])
        with col2:
            st.metric("Discharged Patients", stats.iloc[0]['Discharged'])
        with col3:
            st.metric("Unique Patients", stats.iloc[0]['UniquePatients'])
        with col4:
            st.metric("Avg. Stay Duration", f"{stats.iloc[0]['AvgStayDuration']:.1f} days")

        def show_admission_trends(start_date: str, end_date: str):
            """Show admission trends visualization"""
            trends = DatabaseConnection.run_query(f"""
                SELECT 
                    CAST(AdmissionDate as DATE) as Date,
                    COUNT(*) as AdmissionCount,
                    COUNT(DISTINCT PatientID) as UniquePatients
                FROM Admission
                WHERE AdmissionDate BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY CAST(AdmissionDate as DATE)
                ORDER BY Date
            """)

            if not trends.empty:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=trends['Date'],
                    y=trends['AdmissionCount'],
                    name='Total Admissions',
                    mode='lines+markers',
                    line=dict(color='#2E86C1', width=2)
                ))

                fig.add_trace(go.Scatter(
                    x=trends['Date'],
                    y=trends['UniquePatients'],
                    name='Unique Patients',
                    mode='lines+markers',
                    line=dict(color='#1ABC9C', width=2)
                ))

                fig.update_layout(
                    title='Daily Admission Trends',
                    xaxis_title='Date',
                    yaxis_title='Number of Admissions',
                    height=400,
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

# Main application components and integration
def main():
    """Main application entry point"""
    initialize_session_state()

    # Load custom CSS
    load_custom_css()

    # Create navigation
    page = create_navigation()

    # Update session state
    st.session_state.page = page

    # Route to appropriate page
    route_page(page)


def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        layout="wide",
        initial_sidebar_state="expanded"
    )


def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = None
    if 'selected_doctor' not in st.session_state:
        st.session_state.selected_doctor = None
    if 'filters' not in st.session_state:
        st.session_state.filters = {}


def load_custom_css():
    """Load additional custom CSS styles"""
    st.markdown("""
        <style>
        /* Additional Custom Styles */
        .hospital-header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
        }

        .metric-container {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }

        .notification-badge {
            background-color: red;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }

        /* Enhanced Table Styling */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            border-radius: 0.5rem;
            overflow: hidden;
        }

        .styled-table th {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            text-align: left;
        }

        .styled-table td {
            padding: 1rem;
            border-bottom: 1px solid #f0f0f0;
        }

        /* Form Styling */
        .styled-form {
            background-color: white;
            padding: 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Status Indicators */
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-weight: 500;
            text-align: center;
            display: inline-block;
        }

        /* Enhanced Card Styling */
        .enhanced-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s ease;
        }

        .enhanced-card:hover {
            transform: translateY(-2px);
        }
        </style>
    """, unsafe_allow_html=True)


def show_header():
    """Display application header with notifications"""
    with st.container():
        st.markdown("""
            <div class="hospital-header">
                <h1>Hospital Management System</h1>
            </div>
        """, unsafe_allow_html=True)

        # Show notifications if any
        show_notifications()


def show_notifications():
    """Display system notifications"""
    notifications = get_notifications()
    if notifications:
        with st.sidebar:
            st.markdown("### Notifications")
            for notif in notifications:
                st.markdown(f"""
                    <div class="notification-item">
                        <p>{notif['message']}</p>
                        <small>{notif['timestamp']}</small>
                    </div>
                """, unsafe_allow_html=True)


def get_notifications():
    """Get system notifications"""
    try:
        notifications = DatabaseConnection.run_query("""
            SELECT 
                'Upcoming appointment: ' + p.FirstName + ' ' + p.LastName as message,
                a.AppointmentDate as timestamp
            FROM Appointment a
            JOIN Patient p ON a.PatientID = p.PatientID
            WHERE a.Status = 'Scheduled'
            AND a.AppointmentDate BETWEEN GETDATE() AND DATEADD(HOUR, 24, GETDATE())
            ORDER BY timestamp DESC
        """)

        return notifications if not notifications.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"Error getting notifications: {str(e)}")
        return pd.DataFrame()


def show_notifications():
    """Display system notifications"""
    notifications = get_notifications()
    if not notifications.empty:
        with st.sidebar:
            st.markdown("### Notifications")
            for _, notif in notifications.iterrows():
                st.markdown(f"""
                    <div class="notification-item">
                        <p>{notif['message']}</p>
                        <small>{notif['timestamp']}</small>
                    </div>
                """, unsafe_allow_html=True)


def route_page(page):
    """Route to appropriate page based on selection"""
    show_header()

    try:
        if page == "Dashboard":
            show_dashboard()
        elif page == "Patients":
            show_patients()
        elif page == "Doctors":
            show_doctors()
        elif page == "Appointments":
            show_appointments()
        elif page == "Admissions":
            show_admissions()
    except Exception as e:
        handle_error(e, f"routing to {page}")


class SystemMonitor:
    """Monitor system metrics and performance"""

    @staticmethod
    def check_database_connection():
        """Check database connection status"""
        try:
            conn = DatabaseConnection.get_connection()
            if conn:
                conn.close()
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_system_metrics():
        """Get system performance metrics"""
        metrics = {
            'database_connected': SystemMonitor.check_database_connection(),
            'active_sessions': len(st.session_state),
            'last_updated': datetime.now().strftime(Config.DATETIME_FORMAT)
        }
        return metrics


def show_system_status():
    """Display system status in sidebar"""
    with st.sidebar:
        st.markdown("### System Status")
        metrics = SystemMonitor.get_system_metrics()

        status_color = "green" if metrics['database_connected'] else "red"
        st.markdown(f"""
            <div style="color: {status_color};">
                ● Database Connection: {'Connected' if metrics['database_connected'] else 'Disconnected'}
            </div>
        """, unsafe_allow_html=True)

        st.write(f"Last Updated: {metrics['last_updated']}")


def handle_error(error: Exception, context: str):
    """Centralized error handling"""
    error_message = str(error)
    logging.error(f"Error in {context}: {error_message}")

    if "database" in error_message.lower():
        st.error("Database error occurred. Please try again later.")
    elif "permission" in error_message.lower():
        st.error("You don't have permission to perform this action.")
    else:
        st.error(f"An error occurred: {error_message}")


# Application entry point
if __name__ == "__main__":
    try:
        main()
        show_system_status()
    except Exception as e:
        handle_error(e, "main application")