-- SECOND-LIFE MEDICAL RECORDS: DATABASE SCHEMA
-- This schema enforces immutability and patient-centric access control.

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS medical_records, audit_logs, consents, users;
DROP VIEW IF EXISTS v_active_patients;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Identity & Profile Management
-- Design Note: Denormalized for simplicity, though strict 3NF would separate roles.
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'provider', 'patient') NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    dob DATE, -- Date of Birth (better than Age for data consistency)
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'),
    sex ENUM('Male', 'Female', 'Other'),
    weight FLOAT, 
    height FLOAT  
);

-- 2. Immutable Medical History (Append-Only)
CREATE TABLE medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    linked_record_id INT NULL, -- For traceability of corrections
    diagnosis TEXT NOT NULL,
    bp VARCHAR(20),       
    pulse INT,            
    temp FLOAT,           
    ecg TEXT,             
    medicines TEXT,       
    patient_status ENUM('Stable', 'Critical', 'Discharged') DEFAULT 'Stable',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(id),
    FOREIGN KEY (provider_id) REFERENCES users(id),
    FOREIGN KEY (linked_record_id) REFERENCES medical_records(id)
);

-- 3. Patient-Centric Consent (Time-Bound Access Control)
CREATE TABLE consents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    expires_at DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES users(id),
    FOREIGN KEY (provider_id) REFERENCES users(id)
);

-- 4. Secure Views (Demonstrates Database-Level Security & Derived Attributes)
CREATE VIEW v_active_patients AS
SELECT DISTINCT 
    u.*, 
    TIMESTAMPDIFF(YEAR, u.dob, CURDATE()) AS calculated_age, -- Dynamically calculate age
    c.expires_at, 
    c.provider_id as authorized_provider_id
FROM users u
JOIN consents c ON u.id = c.patient_id
WHERE c.expires_at >= CURDATE();

-- 5. Transparency & Traceability (Audit Logs)
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    executed_query TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Immutability Triggers (The "Magic" Logic)
DELIMITER //
CREATE TRIGGER block_record_update BEFORE UPDATE ON medical_records 
FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Second-Life Policy: Records are immutable.';
END //

CREATE TRIGGER block_record_delete BEFORE DELETE ON medical_records 
FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Second-Life Policy: Records cannot be deleted.';
END //
DELIMITER ;

-- 7. Seed Data for Testing
INSERT INTO users (username, password, role, full_name, dob, blood_group) VALUES 
('admin', 'passkey_12345', 'admin', 'System Administrator', '1985-01-01', 'O+'),
('trehan', 'doctor_12345', 'provider', 'Dr. Naresh Trehan (Cardio)', '1960-05-15', 'A+'),
('dada', 'doctor_12345', 'provider', 'Dr. Tanuj Dada (Opthalm)', '1965-08-20', 'B+'),
('gupta', 'doctor_12345', 'provider', 'Dr. Shalini Gupta (Dental)', '1975-03-10', 'O-'),
('farouqee', 'doctor_12345', 'provider', 'Dr. Kamran Farouqee (Trauma)', '1980-11-25', 'AB+'),
('minz', 'doctor_12345', 'provider', 'Dr. Minz (Neuro)', '1972-02-14', 'B-'),
('madan', 'doctor_12345', 'provider', 'Dr. Karan Madan (Pulmo)', '1982-06-30', 'A-'),
('sharan', 'doctor_12345', 'provider', 'Dr. Swapna Sharan (Gynec)', '1978-09-12', 'O+'),
('sushma', 'doctor_12345', 'provider', 'Dr. Sushma (Paediatric)', '1985-04-05', 'B+'),
('batra', 'doctor_12345', 'provider', 'Dr. Atul Batra (Radio)', '1983-12-01', 'AB-');

INSERT INTO users (username, password, role, full_name, dob, blood_group, sex, weight, height) VALUES 
('patient_zero', 'pat123', 'patient', 'John Doe', '1994-10-10', 'O+', 'Male', 75.5, 180.0);
