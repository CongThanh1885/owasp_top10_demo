# 🚀 HƯỚNG DẪN KHỞI CHẠY VÀ KIỂM THỬ ỨNG DỤNG (README)

Tài liệu này hướng dẫn cách khởi chạy ứng dụng web thử nghiệm trong môi trường Docker, đồng thời mô tả chi tiết **kết quả phản hồi (Response) thực tế** trên **Burp Suite** và **Postman** khi tiến hành kiểm thử trên cả hai phiên bản: **Ứng dụng chứa lỗ hổng (Vulnerable App)** và **Ứng dụng đã khắc phục (Fixed App)**.

---

## 🛠️ 1. HƯỚNG DẪN KHỞI CHẠY (DEPLOYMENT)

### 🔴 Cách 1: Chạy ứng dụng có lỗ hổng (Vulnerable App)
```bash
cd web_app
docker build -t web_app_vuln .
docker run -p 5656:5656 web_app_vuln
```
🌐 **Địa chỉ truy cập:** `http://localhost:5656`

---

### 🟢 Cách 2: Chạy ứng dụng đã khắc phục (Fixed App)
```bash
cd web_app_fixed
docker build -t web_app_fixed .
docker run -p 5656:5656 web_app_fixed
```
🌐 **Địa chỉ truy cập:** `http://localhost:5656`

---

## 🧪 2. CHI TIẾT KIỂM THỬ BẰNG BURP SUITE & POSTMAN

### 1. SQL Injection (SQLi) - Endpoint: `POST /login`

#### 📡 Yêu cầu gửi đi (Request Vector)
* **URL:** `POST http://localhost:5656/login`
* **Header:** `Content-Type: application/x-www-form-urlencoded`
* **Body / Payload:**
  ```http
  username=' OR '1'='1&password=' OR '1'='1 (Có thể thay bằng ' OR '1'='1' -- / ' OR '1'='1' #)
  ```

#### 📊 Kết quả kiểm thử đối chiếu:

* **Trên Burp Suite (Repeater / Intercept):**
  * **🔴 App Vuln:**
    * **HTTP Status:** `200 OK`
    * **Response Body:** `Login success!`
    * *Giải thích:* CSDL SQLite xử lý payload `' OR '1'='1`, biểu thức trả về `TRUE` làm câu lệnh SQL bỏ qua mật khẩu.
  * **🟢 App Fixed:**
    * **HTTP Status:** `200 OK`
    * **Response Body:** `Invalid credentials!`
    * *Giải thích:* Dữ liệu đầu vào được xử lý bằng Parameterized Query (`?`), chuỗi payload bị coi là giá trị văn bản thuần túy và không tìm thấy user tương ứng.

* **Trên Postman:**
  * **Body tab:** Chọn `x-www-form-urlencoded` ➔ Key `username`: `' OR '1'='1`, Key `password`: `' OR '1'='1`.
  * **🔴 App Vuln:** Tab Response xuất hiện chuỗi **"Login success!"**.
  * **🟢 App Fixed:** Tab Response xuất hiện chuỗi **"Invalid credentials!"**.

---

### 2. Cross-Site Scripting (XSS) - Endpoint: `POST /comment`

#### 📡 Yêu cầu gửi đi (Request Vector)
* **URL:** `POST http://localhost:5656/comment`
* **Header:** `Content-Type: application/x-www-form-urlencoded`
* **Body / Payload:**
  ```http
  comment=<script>alert('XSS')</script>
  ```

#### 📊 Kết quả kiểm thử đối chiếu:

* **Trên Burp Suite (Repeater / Intercept):**
  * **🔴 App Vuln:**
    * **HTTP Status:** `200 OK`
    * **Response Body:**
      ```html
      You posted: <script>alert('XSS')</script>
      ```
    * *Giải thích:* Mã HTML/JavaScript nguyên bản trả về client, trình duyệt sẽ tự động thực thi làm bật hộp thoại alert.
  * **🟢 App Fixed:**
    * **HTTP Status:** `200 OK`
    * **Response Body:**
      ```html
      You posted: &lt;script&gt;alert('XSS')&lt;/script&gt;
      ```
    * *Giải thích:* Ký tự `<` và `>` đã được biến đổi thành thực thể an toàn `&lt;` và `&gt;` nhờ hàm `html.escape()`.

* **Trên Postman:**
  * **Body tab:** Chọn `x-www-form-urlencoded` ➔ Key `comment`: `<script>alert('XSS')</script>`.
  * **🔴 App Vuln:** Phản hồi chứa thẻ `<script>` chưa qua xử lý.
  * **🟢 App Fixed:** Phản hồi hiển thị chuỗi đã qua mã hóa HTML Entities (`&lt;script&gt;...`).

---

### 3. Cross-Site Request Forgery (CSRF) - Endpoint: `POST /change-password`

#### 📡 Yêu cầu gửi đi (Request Vector - Không chứa Anti-CSRF Token)
* **URL:** `POST http://localhost:5656/change-password`
* **Header:** 
  * `Content-Type: application/x-www-form-urlencoded`
  * `Cookie: session=<giá_trị_session_từ_browser>`
* **Body:**
  ```http
  username=admin&newPassword=111
  ```

#### 📊 Kết quả kiểm thử đối chiếu:

* **Trên Burp Suite (Repeater / Intercept):**
  * **🔴 App Vuln:**
    * **HTTP Status:** `200 OK`
    * **Response Body:** `Password changed!`
    * *Giải thích:* Hệ thống chỉ kiểm tra session cookie hợp lệ mà không xác thực nguồn gốc request hay token, dẫn đến mật khẩu bị đổi thành `111`.
  * **🟢 App Fixed (Thiếu token hoặc token sai):**
    * **HTTP Status:** `403 Forbidden`
    * **Response Body:** `CSRF detected!`
    * *Giải thích:* Server đối chiếu `csrf_token` gửi lên từ form với `session["csrf_token"]`, phát hiện bất thường và chặn request.

* **Trên Postman:**
  * **🔴 App Vuln:** Gửi request không có `csrf_token` ➔ Trả về `200 OK` với text **"Password changed!"**.
  * **🟢 App Fixed:** 
    * Nếu thiếu `csrf_token` ➔ Trả về `403 Forbidden` với text **"CSRF detected!"**.
    * Khi truyền đúng `csrf_token` (lấy từ GET request `/change-password`) ➔ Trả về `200 OK` với text **"Password changed!"**.

---

### 4. Insecure File Upload - Endpoint: `POST /upload`

#### 📡 Yêu cầu gửi đi (Request Vector - Web Shell Payload)
* **URL:** `POST http://localhost:5656/upload`
* **Header:** `Content-Type: multipart/form-data`
* **Body (form-data):**
  * Key: `file` | Type: `File` | Selected file: `shell.php` hoặc `shell.py`

#### 📊 Kết quả kiểm thử đối chiếu:

* **Trên Burp Suite (Repeater / Intercept):**
  * **🔴 App Vuln:**
    * **HTTP Status:** `200 OK`
    * **Response Body:** `File uploaded: shell.php`
    * *Giải thích:* File `.php` được lưu thẳng vào thư mục `uploads/` trên server mà không kiểm tra đuôi file hay nội dung.
  * **🟢 App Fixed (Gửi file độc hại .php):**
    * **HTTP Status:** `400 Bad Request`
    * **Response Body:** `Invalid file type!`
    * *Giải thích:* Hệ thống kiểm tra đuôi file nằm ngoài danh sách Whitelist (`png`, `jpg`, `jpeg`, `gif`) nên từ chối xử lý.
  * **🟢 App Fixed (Gửi file hợp lệ .jpg):**
    * **HTTP Status:** `200 OK`
    * **Response Body:** `File uploaded safely!`
    * *Giải thích:* File hợp lệ được chuẩn hóa tên qua `secure_filename()` và lưu trữ an toàn.

* **Trên Postman:**
  * **Body tab:** Chọn `form-data` ➔ Key `file` chọn dạng File ➔ Tải lên `shell.php`.
  * **🔴 App Vuln:** Trả về `200 OK` - **"File uploaded: shell.php"**.
  * **🟢 App Fixed:** Trả về `400 Bad Request` - **"Invalid file type!"**. Khi đổi sang chọn file `image.png`, trả về `200 OK` - **"File uploaded safely!"**.

---

## 🎯 3. KẾT LUẬN

| Tiêu chí | 🔴 `web_app/` (Vulnerable) | 🟢 `web_app_fixed/` (Fixed) |
| :--- | :--- | :--- |
| **Bản chất** | Mô phỏng thực tế 4 lỗ hổng OWASP Top 10 | Áp dụng các nguyên lý phòng thủ chuẩn |
| **SQLi Protection** | ❌ Không có (Nối chuỗi trực tiếp) | ✅ Có (Parameterized Query `?`) |
| **XSS Protection** | ❌ Không có (Render Raw HTML) | ✅ Có (HTML Escaping `html.escape`) |
| **CSRF Protection** | ❌ Không có | ✅ Có (Synchronizer Token Pattern) |
| **File Upload** | ❌ Không kiểm tra đuôi/tên file | ✅ Whitelist Extension & `secure_filename()` |
| **Kiểm thử thực tế** | Dễ dàng khai thác qua Burp Suite / Postman | Mọi request độc hại đều bị chặn/xử lý an toàn |