-- Create the database
CREATE DATABASE SimpleHospitalDB;
GO

USE SimpleHospitalDB;
GO

-- Create Gender table
CREATE TABLE Gender (
    GenderID INT PRIMARY KEY IDENTITY(1,1),
    Name VARCHAR(10) NOT NULL
);
GO

-- Create Department table
CREATE TABLE Department (
    DepartmentID INT PRIMARY KEY IDENTITY(1,1),
    Name VARCHAR(100) NOT NULL
);
GO

-- Create Patient table
CREATE TABLE Patient (
    PatientID INT PRIMARY KEY IDENTITY(1,1),
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    GenderID INT REFERENCES Gender(GenderID),
    DateOfBirth DATE,
    ContactNumber VARCHAR(15),
    Email VARCHAR(100),
    Address VARCHAR(200),
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create Doctor table
CREATE TABLE Doctor (
    DoctorID INT PRIMARY KEY IDENTITY(1,1),
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    GenderID INT REFERENCES Gender(GenderID),
    DepartmentID INT REFERENCES Department(DepartmentID),
    Specialization VARCHAR(100),
    ContactNumber VARCHAR(15),
    Email VARCHAR(100),
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create Appointment table
CREATE TABLE Appointment (
    AppointmentID INT PRIMARY KEY IDENTITY(1,1),
    PatientID INT REFERENCES Patient(PatientID),
    DoctorID INT REFERENCES Doctor(DoctorID),
    AppointmentDate DATETIME NOT NULL,
    Status VARCHAR(20) DEFAULT 'Scheduled', -- Scheduled, Completed, Cancelled
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Create Room table
CREATE TABLE Room (
    RoomID INT PRIMARY KEY IDENTITY(1,1),
    RoomNumber VARCHAR(10) NOT NULL,
    RoomType VARCHAR(50), -- General, Private, ICU
    Status VARCHAR(20) DEFAULT 'Available' -- Available, Occupied
);
GO

-- Create Admission table
CREATE TABLE Admission (
    AdmissionID INT PRIMARY KEY IDENTITY(1,1),
    PatientID INT REFERENCES Patient(PatientID),
    DoctorID INT REFERENCES Doctor(DoctorID),
    RoomID INT REFERENCES Room(RoomID),
    AdmissionDate DATETIME NOT NULL,
    DischargeDate DATETIME,
    Status VARCHAR(20) DEFAULT 'Admitted', -- Admitted, Discharged
    CreatedDate DATETIME DEFAULT GETDATE()
);
GO

-- Insert sample data
-- Gender
INSERT INTO Gender (Name) VALUES ('Male'), ('Female');
GO

-- Departments
INSERT INTO Department (Name) VALUES
('General Medicine'),
('Pediatrics'),
('Cardiology'),
('Orthopedics'),
('Surgery');
GO

-- Sample Rooms
INSERT INTO Room (RoomNumber, RoomType, Status) VALUES
('101', 'General', 'Available'),
('102', 'General', 'Available'),
('201', 'Private', 'Available'),
('202', 'Private', 'Available'),
('301', 'ICU', 'Available');
GO

-- Sample Patients
INSERT INTO Patient (FirstName, LastName, GenderID, DateOfBirth, ContactNumber, Email, Address) VALUES
('John', 'Doe', 1, '1990-05-15', '1234567890', 'john@email.com', '123 Main St'),
('Jane', 'Smith', 2, '1985-08-22', '9876543210', 'jane@email.com', '456 Oak Ave'),
('Mike', 'Johnson', 1, '1978-03-10', '5555555555', 'mike@email.com', '789 Pine Rd');
GO

-- Sample Doctors
INSERT INTO Doctor (FirstName, LastName, GenderID, DepartmentID, Specialization, ContactNumber, Email) VALUES
('Dr. Sarah', 'Wilson', 2, 1, 'General Physician', '1112223333', 'sarah@hospital.com'),
('Dr. James', 'Brown', 1, 3, 'Cardiologist', '4445556666', 'james@hospital.com'),
('Dr. Emily', 'Davis', 2, 2, 'Pediatrician', '7778889999', 'emily@hospital.com');
GO

-- Sample Appointments
INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, Status) VALUES
(1, 1, DATEADD(day, 1, GETDATE()), 'Scheduled'),
(2, 2, DATEADD(day, 2, GETDATE()), 'Scheduled'),
(3, 3, DATEADD(day, 3, GETDATE()), 'Scheduled');
GO

-- Sample Admissions
INSERT INTO Admission (PatientID, DoctorID, RoomID, AdmissionDate, Status) VALUES
(1, 1, 1, GETDATE(), 'Admitted'),
(2, 2, 3, DATEADD(day, -5, GETDATE()), 'Admitted');
GO

-- Create View for Patient Details
CREATE VIEW vw_PatientDetails AS
SELECT 
    p.PatientID,
    p.FirstName + ' ' + p.LastName AS PatientName,
    g.Name AS Gender,
    p.DateOfBirth,
    p.ContactNumber,
    p.Email,
    p.Address
FROM Patient p
JOIN Gender g ON p.GenderID = g.GenderID;
GO

-- Create View for Doctor Details
CREATE VIEW vw_DoctorDetails AS
SELECT 
    d.DoctorID,
    d.FirstName + ' ' + d.LastName AS DoctorName,
    g.Name AS Gender,
    dept.Name AS Department,
    d.Specialization,
    d.ContactNumber,
    d.Email
FROM Doctor d
JOIN Gender g ON d.GenderID = g.GenderID
JOIN Department dept ON d.DepartmentID = dept.DepartmentID;
GO

-- Create View for Appointment Details
CREATE VIEW vw_AppointmentDetails AS
SELECT 
    a.AppointmentID,
    p.FirstName + ' ' + p.LastName AS PatientName,
    d.FirstName + ' ' + d.LastName AS DoctorName,
    a.AppointmentDate,
    a.Status
FROM Appointment a
JOIN Patient p ON a.PatientID = p.PatientID
JOIN Doctor d ON a.DoctorID = d.DoctorID;
GO

-- Create View for Admission Details
CREATE VIEW vw_AdmissionDetails AS
SELECT 
    a.AdmissionID,
    p.FirstName + ' ' + p.LastName AS PatientName,
    d.FirstName + ' ' + d.LastName AS DoctorName,
    r.RoomNumber,
    r.RoomType,
    a.AdmissionDate,
    a.DischargeDate,
    a.Status
FROM Admission a
JOIN Patient p ON a.PatientID = p.PatientID
JOIN Doctor d ON a.DoctorID = d.DoctorID
JOIN Room r ON a.RoomID = r.RoomID;
GO


