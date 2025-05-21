CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcripts (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT        NOT NULL,
  transcript    TEXT       NOT NULL,
  created_at    TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS degreqs (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  user_id      INT          NOT NULL,
  major        VARCHAR(255) NOT NULL,
  requirements MEDIUMTEXT   NOT NULL,
  recorded_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS preferences (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT          NOT NULL,
  question    VARCHAR(255) NOT NULL,
  answer      TEXT,
  recorded_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_pref (user_id, question),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- Add this to your db/init.sql file or execute as a separate migration

CREATE TABLE IF NOT EXISTS schedules (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT          NOT NULL,
  schedule_text  MEDIUMTEXT   NOT NULL,
  created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);