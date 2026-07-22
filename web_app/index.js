const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const multer = require('multer');
const path = require('path');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.use(bodyParser.urlencoded({ extended: true }));

// Database setup
const db = new sqlite3.Database(':memory:');
db.serialize(() => {
    db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)");
    db.run("INSERT INTO users (username, password) VALUES ('admin','admin123')");
});

// Serve index.html at root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Login (SQLi vulnerable)
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    const query = `SELECT * FROM users WHERE username='${username}' AND password='${password}'`; // ❌ vulnerable
    db.get(query, (err, row) => {
        if (row) res.send("Login success!");
        else res.send("Login failed!");
    });
});

// Comment (XSS vulnerable)
app.post('/comment', (req, res) => {
    const comment = req.body.comment;
    res.send(`You posted: ${comment}`); // ❌ vulnerable
});

// Change password (CSRF vulnerable)
app.post('/change-password', (req, res) => {
    const { username, newPassword } = req.body;
    db.run(`UPDATE users SET password='${newPassword}' WHERE username='${username}'`);
    res.send("Password changed!");
});

// File upload (Insecure)
app.post('/upload', upload.single('file'), (req, res) => {
    res.send(`File uploaded: ${req.file.originalname}`); // ❌ no validation
});

// Run server on port 5656
app.listen(5656, () => console.log("App running on http://localhost:5656"));
