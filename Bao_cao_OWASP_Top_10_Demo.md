# 📑 BÁO CÁO PHÂN TÍCH VÀ KHẮC PHỤC LỖ HỔNG OWASP TOP 10

---

## 📄 TỔNG QUAN

Báo cáo này đối chiếu chi tiết đoạn mã nguồn ban đầu được viết bằng **Node.js (Express)** chứa 4 lỗ hổng bảo mật nghiêm trọng và phiên bản được viết lại bằng **Python (Flask)** đã áp dụng các giải pháp phòng thủ triệt để.

---

## 📊 BẢNG TỔNG QUAN DỰ ÁN

| Lỗ hổng | Mức độ rủi ro | Trạng thái Express.js (Chứa lỗi) | Trạng thái Python/Flask (Đã khắc phục) |
| :--- | :---: | :--- | :--- |
| **SQL Injection** | 🔴 **Critical** | Nối chuỗi trực tiếp vào query | Dùng Parameterized Query (`?`) |
| **Cross-Site Scripting (XSS)** | 🟠 **High** | Phản hồi raw HTML | Mã hóa ký tự bằng `html.escape()` |
| **CSRF** | 🟡 **Medium** | Không có cơ chế xác thực Token | Sinh và kiểm tra `csrf_token` trong Session |
| **Insecure File Upload** | 🔴 **Critical** | Lưu trực tiếp, không kiểm tra file | Kiểm tra đuôi file & dùng `secure_filename()` |

---

## 1. SQL INJECTION (SQLi)

### 🔴 Mã nguồn vi phạm (Node.js/Express)
```javascript
// ❌ Dữ liệu từ user được nối chuỗi trực tiếp
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    const query = `SELECT * FROM users WHERE username='${username}' AND password='${password}'`;
    db.get(query, (err, row) => {
        if (row) res.send("Login success!");
        else res.send("Login failed!");
    });
});
```
* **Kịch bản khai thác:** Nhập username là `' OR '1'='1` để bypass cơ chế đăng nhập.

### 🟢 Mã nguồn đã khắc phục (Python/Flask)
```python
# ✅ Sử dụng Parameterized Query với dấu ?
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return "Login success!"
        return "Invalid credentials!"
    return render_template("login.html")
```
* **Cơ chế khắc phục:** Trình quản lý CSDL SQLite xử lý `username` và `password` như các giá trị hằng số (Literal Values), vô hiệu hóa hoàn toàn khả năng can thiệp vào cú pháp lệnh SQL.

---

## 2. CROSS-SITE SCRIPTING (XSS)

### 🔴 Mã nguồn vi phạm (Node.js/Express)
```javascript
// ❌ Phản hồi trực tiếp HTML chứa dữ liệu người dùng
app.post('/comment', (req, res) => {
    const comment = req.body.comment;
    res.send(`You posted: ${comment}`);
});
```
* **Kịch bản khai thác:** Nhập `<script>alert('XSS')</script>` hoặc mã đánh cắp Session Cookie để thực thi JavaScript trên trình duyệt nạn nhân.

### 🟢 Mã nguồn đã khắc phục (Python/Flask)
```python
# ✅ Mã hóa ký tự đặc biệt thành HTML Entities
@app.route("/comment", methods=["GET","POST"])
def comment():
    if request.method == "POST":
        comment = request.form["comment"]
        safe_comment = html.escape(comment)
        return render_template("comment.html", comment=safe_comment)
    return render_template("comment.html", comment=None)
```
* **Cơ chế khắc phục:** Hàm `html.escape()` chuyển đổi các ký tự nguy hiểm như `<`, `>`, `&`, `"`, `'` thành dạng thực thể HTML (ví dụ: `<` thành `&lt;`), khiến trình duyệt hiển thị dữ liệu dạng văn bản thuần túy thay vì thực thi mã.

---

## 3. CROSS-SITE REQUEST FORGERY (CSRF)

### 🔴 Mã nguồn vi phạm (Node.js/Express)
```javascript
// ❌ Đổi mật khẩu mà không kiểm tra tính hợp lệ của request
app.post('/change-password', (req, res) => {
    const { username, newPassword } = req.body;
    db.run(`UPDATE users SET password='${newPassword}' WHERE username='${username}'`);
    res.send("Password changed!");
});
```
* **Kịch bản khai thác:** Hacker lừa người dùng đã đăng nhập truy cập vào trang web độc hại chứa form ẩn tự động submit request tới `/change-password` để đổi mật khẩu.

### 🟢 Mã nguồn đã khắc phục (Python/Flask)
```python
# ✅ Tạo và xác thực CSRF Token ngẫu nhiên
@app.route("/change-password", methods=["GET","POST"])
def change_password():
    if request.method == "GET":
        token = secrets.token_hex(16)
        session["csrf_token"] = token
        return render_template("change_password.html", token=token)
    else:
        if request.form.get("csrf_token") != session.get("csrf_token"):
            return "CSRF detected!", 403
            
        username = request.form["username"]
        newPassword = request.form["newPassword"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE username=?", (newPassword, username))
        conn.commit()
        conn.close()
        return "Password changed!"
```
* **Cơ chế khắc phục:** Sử dụng mô hình **Synchronizer Token Pattern**. Mỗi khi mở trang đổi mật khẩu, hệ thống sinh ra một chuỗi ngẫu nhiên (`token`) lưu ở `session` và gửi về form. Khi POST dữ liệu lên, server đối chiếu token từ form với token lưu trong session. Hacker từ trang web khác không thể đoán được token này.

---

## 4. INSECURE FILE UPLOAD

### 🔴 Mã nguồn vi phạm (Node.js/Express)
```javascript
// ❌ Tải file lên trực tiếp mà không kiểm tra định dạng hoặc tên file
app.post('/upload', upload.single('file'), (req, res) => {
    res.send(`File uploaded: ${req.file.originalname}`);
});
```
* **Kịch bản khai thác:** Hacker có thể upload Web Shell (`shell.php`, `shell.py`, `shell.js`) hoặc các file chứa tên nguy hiểm như `../../etc/passwd` (Path Traversal) để chiếm quyền điều khiển server.

### 🟢 Mã nguồn đã khắc phục (Python/Flask)
```python
# ✅ Kiểm tra đuôi file và chuẩn hóa tên file
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["GET","POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return "File uploaded safely!"
        return "Invalid file type!", 400
    return render_template("upload.html")
```
* **Cơ chế khắc phục:**
  1. **Whitelisting Extension:** Hàm `allowed_file()` chỉ chấp nhận các tập tin hình ảnh (`png`, `jpg`, `jpeg`, `gif`).
  2. **Sanitize Filename:** Hàm `secure_filename()` của Werkzeug loại bỏ hoàn toàn các ký tự độc hại như `/`, `\`, `..` để phòng chống tấn công Path Traversal.

---

## 🎯 TỔNG KẾT

Phiên bản **Python/Flask** đã giải quyết triệt để cả 4 lỗ hổng của phiên bản **Node.js/Express** ban đầu bằng các nguyên tắc bảo mật tiêu chuẩn:
1. **Tách biệt Mã & Dữ liệu:** Dùng Parameterized Queries.
2. **Mã hóa Output:** Dùng HTML Escaping trước khi hiển thị dữ liệu.
3. **Xác thực Request Origin:** Dùng Anti-CSRF Tokens ngẫu nhiên.
4. **Giới hạn & Chuẩn hóa Input:** Whitelist định dạng file và Sanitize đường dẫn lưu trữ.