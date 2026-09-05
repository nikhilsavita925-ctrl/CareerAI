-- ============================================================
-- AI Internship Recommendation Engine - Database Schema
-- Run this once to create the database and tables:
--   mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS internship_ai;
USE internship_ai;

-- ---------- Users ----------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    fullname      VARCHAR(120)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    phone         VARCHAR(20),
    college       VARCHAR(150),
    course        VARCHAR(100),
    semester      INT,
    skills        TEXT,                     -- comma separated, entered at registration
    password_hash VARCHAR(255)  NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Internships (sample dataset the recommender matches against) ----------
CREATE TABLE IF NOT EXISTS internships (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(150) NOT NULL,
    company          VARCHAR(150) NOT NULL,
    location         VARCHAR(100),
    duration_months  INT,
    stipend          VARCHAR(50),
    required_skills  TEXT NOT NULL,          -- comma separated
    description      TEXT
);

-- ---------- Resumes uploaded by users ----------
CREATE TABLE IF NOT EXISTS resumes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    filename      VARCHAR(255) NOT NULL,
    extracted_text MEDIUMTEXT,
    extracted_skills TEXT,
    ats_score     INT,
    uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ---------- Saved / applied recommendations (optional tracking) ----------
CREATE TABLE IF NOT EXISTS applications (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    internship_id  INT NOT NULL,
    match_score    DECIMAL(5,2),
    status         VARCHAR(30) DEFAULT 'saved',   -- saved / applied
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE
);

-- ---------- Sample internship data so recommendations work out of the box ----------
INSERT INTO internships (title, company, location, duration_months, stipend, required_skills, description) VALUES
('Python Backend Developer Intern', 'TechNova Pvt Ltd', 'Remote', 3, '₹10,000/month', 'python,flask,mysql,rest api,git', 'Work on backend APIs using Flask and MySQL.'),
('Frontend Developer Intern', 'PixelWorks', 'Bengaluru', 2, '₹8,000/month', 'html,css,javascript,react,bootstrap', 'Build responsive UI components for web apps.'),
('Data Analyst Intern', 'InsightHub', 'Remote', 3, '₹12,000/month', 'python,pandas,sql,excel,data visualization', 'Analyze datasets and build dashboards.'),
('Machine Learning Intern', 'NeuronLabs', 'Pune', 4, '₹15,000/month', 'python,machine learning,numpy,pandas,scikit-learn', 'Build and evaluate ML models.'),
('Full Stack Developer Intern', 'CodeCraft', 'Hyderabad', 3, '₹10,000/month', 'javascript,node.js,react,mysql,html,css', 'End-to-end web application development.'),
('Java Backend Intern', 'Enterprize Solutions', 'Remote', 3, '₹9,000/month', 'java,spring boot,mysql,rest api', 'Develop backend microservices in Java.'),
('UI/UX Design Intern', 'DesignSpark', 'Mumbai', 2, '₹7,000/month', 'figma,ui design,ux research,adobe xd', 'Design user interfaces and conduct usability tests.'),
('Cloud Computing Intern', 'CloudBridge', 'Remote', 3, '₹11,000/month', 'aws,linux,docker,python,networking', 'Support cloud infrastructure and deployments.'),
('Digital Marketing Intern', 'MarketMinds', 'Delhi', 2, '₹6,000/month', 'seo,content writing,social media,analytics', 'Plan and execute digital marketing campaigns.'),
('Android App Development Intern', 'AppForge', 'Chennai', 3, '₹9,000/month', 'java,kotlin,android studio,xml,firebase', 'Build and test Android mobile applications.');

-- ---------- Pending email-verified registrations ----------
CREATE TABLE IF NOT EXISTS pending_registrations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    fullname        VARCHAR(120) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    college         VARCHAR(150),
    course          VARCHAR(100),
    semester        INT,
    skills          TEXT,
    otp_hash        VARCHAR(255) NOT NULL,
    otp_expires_at  DATETIME NOT NULL,
    otp_verified    TINYINT(1) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
