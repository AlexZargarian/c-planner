CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/* (Optionally) insert a test user, with password “password” hashed via passlib: */
/* INSERT INTO users (email, password_hash)
   VALUES ('test@example.com','<bcrypt-hash-of-password>'); */
