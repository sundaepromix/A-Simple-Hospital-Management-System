# 🏥 Hospital Management System Database

Hey there! Welcome to my Hospital Management System Database project. This is a SQL-based solution I built to help hospitals manage their day-to-day operations more efficiently. Let me walk you through it!

## 📋 What's This All About?

This is a database system that helps hospitals:
- Keep track of patients and doctors
- Manage appointments smoothly
- Handle room assignments
- Track admissions and discharges
- Generate useful reports

## 🛠️ Technologies Used

- SQL Server (Any version from 2016 and up should work fine)
- T-SQL for stored procedures and views

## 🚀 Getting Started

### Prerequisites

- Microsoft SQL Server installed on your machine
- SQL Server Management Studio (SSMS) or any SQL client you prefer
- Basic understanding of SQL queries

### Installation Steps

1. Clone this repository:
git clone https://github.com/sundaepromix/A-Simple-Hospital-Management-System.git

2. Open SQL Server Management Studio

3. Run the scripts in this order:
   - 01_CreateDatabase.sql (Sets up the database)
   - 02_CreateTables.sql (Creates all necessary tables)
   - 03_CreateViews.sql (Sets up helpful views)
   - 04_StoredProcedures.sql (Adds all the stored procedures)
   - 05_SampleData.sql (Populates tables with test data)

## 📊 Database Structure

### Core Tables
- Patient - Stores patient information
- Doctor - Manages doctor details
- Appointment - Handles scheduling
- Room - Tracks hospital rooms
- Admission - Records patient stays
- Department - Lists hospital departments
- Gender - Lookup table for gender

### Views
- vw_PatientDetails - Complete patient information
- vw_DoctorDetails - Detailed doctor profiles
- vw_AppointmentDetails - Comprehensive appointment info
- vw_AdmissionDetails - Full admission records

### Key Stored Procedures
- sp_BookAppointment - Schedule new appointments
- sp_AdmitPatient - Handle patient admissions
- sp_GetDoctorWorkload - Track doctor schedules
- sp_GetRoomAvailability - Check room status

## 🎯 Features

- Appointment Management: No more double bookings!
- Room Tracking: Always know which rooms are available
- Patient Records: Keep patient info organized
- Doctor Schedules: Manage doctor availability
- Report Generation: Get insights when you need them

## 💡 Usage Examples

### Booking an Appointment
EXEC sp_BookAppointment 
    @PatientID = 1,
    @DoctorID = 1,
    @AppointmentDate = '2024-01-10 14:30:00'

### Checking Room Availability
EXEC sp_GetRoomAvailability

### Viewing All Appointments
SELECT * FROM vw_AppointmentDetails

## 🤝 Contributing

Found a bug? Have an idea for an improvement? I'd love to hear from you! Here's how you can help:

1. Fork the repo
2. Create a new branch (git checkout -b cool-new-feature)
3. Make your changes
4. Push to the branch (git push origin cool-new-feature)
5. Open a Pull Request

## 📝 Notes

- This is a basic version meant for learning and customization
- Feel free to modify the code to fit your needs
- If something breaks, check the error logs first
- Made with ❤️ and lots of coffee

## 🔜 Coming Soon

Working on adding:
- Billing system integration
- Medicine inventory tracking
- Staff scheduling module
- Patient medical history
- Insurance processing

## 🐛 Known Issues

- Room allocation might need tweaking for large hospitals
- Some reports could be optimized for better performance
- Working on improving date handling in some procedures

## 📫 Questions?

Got questions? Reach out to me:
- Email: sundaepromix@gmail.com
- Twitter: @sundaepromix
- LinkedIn: https://www.linkedin.com/in/sunday-promise-460961231/
  
---
Made with SQL and enthusiasm by Promise Sunday 

Remember to ⭐ if you found this useful!

---
Last Updated: January 2024
