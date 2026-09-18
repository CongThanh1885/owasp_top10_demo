# Demo OWASP Top 10

Repository này bao gồm hai ứng dụng có chủ đích khác nhau để kiểm thử bảo mật trên máy local:

- `web_app/`: Ứng dụng Node.js/Express chứa bốn lỗ hổng được tạo có chủ đích.
- `web_app_fixed/`: Ứng dụng Flask với các biện pháp khắc phục tương ứng.

Đây là dự án phục vụ đào tạo. Chỉ chạy trên `localhost` hoặc mạng lab được cô lập. Không bao giờ đưa `web_app/` lên Internet hoặc sử dụng lại thông tin đăng nhập của ứng dụng trong hệ thống thực tế.

---

## 1. Yêu cầu chuẩn bị

- Docker Desktop với Linux engine đang chạy.
- Docker Compose v2 (`docker compose version`).
- Không bắt buộc: Semgrep để quét mã nguồn trên máy local.
- Cổng `5656` chưa được sử dụng trên máy host.

## 2. Triển khai trên máy local

### Build cả hai image
```bash
docker compose --profile vulnerable --profile fixed build
```

Khởi động ứng dụng đã khắc phục ở chế độ chạy nền:
```bash
docker compose --profile fixed up -d
curl.exe http://localhost:5656/
```

Dừng ứng dụng trước khi khởi động phiên bản còn lại:
```bash
docker compose --profile fixed down
docker compose --profile vulnerable up -d
curl.exe http://localhost:5656/
```

Các lệnh quản lý vòng đời thường dùng:
```bash
docker compose --profile fixed logs -f
docker compose --profile vulnerable logs -f
docker compose --profile fixed down
docker compose --profile vulnerable down
```

Chỉ chạy một profile tại một thời điểm vì cả hai ứng dụng đều sử dụng cổng `5656` trên host.

## 3. CI/CD và quét mã nguồn

GitHub Actions trong `.github/workflows/ci-cd.yml` chạy khi có pull request và khi push lên nhánh `main` hoặc `master`:

1. Semgrep phải kiểm tra thành công `web_app_fixed`.
2. Semgrep quét `web_app` và tải các phát hiện dự kiến lên dưới dạng artifact.
3. Cả hai Docker image đều được build.
4. Khi push lên `main`, các image được publish lên GitHub Container Registry.

Sau mỗi lần quét, workflow lưu báo cáo Semgrep ở định dạng JSON và SARIF dưới dạng artifact:

- `semgrep-fixed-reports`
- `semgrep-vulnerable-reports`

Chạy bước kiểm tra bắt buộc cho ứng dụng đã khắc phục trên máy local:
```bash
semgrep scan --config p/owasp-top-ten --error --exclude-rule python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host web_app_fixed
```

Quét ứng dụng đào tạo có chủ đích chứa lỗ hổng:
```bash
semgrep scan --config p/owasp-top-ten web_app
```

Xuất báo cáo khi quét local:
```bash
semgrep scan --config p/owasp-top-ten --json-output semgrep-vulnerable.json --sarif-output semgrep-vulnerable.sarif web_app
```

Rule kiểm tra bind host chỉ được loại trừ trong lần quét ứng dụng đã khắc phục vì Flask phải bind tới `0.0.0.0` bên trong container. Image đã khắc phục chạy bằng user không phải root.

## 4. Quy trình pentest

Sử dụng Burp Suite hoặc Postman để gửi request tới `http://localhost:5656`. Khởi động lại container giữa các test case khi cần database in-memory hoặc session mới.

Đối với ứng dụng đã khắc phục, trước tiên mở `GET /change-password` trong cùng một browser hoặc proxy session. Response sẽ tạo session và chứa CSRF token trong form. Sử dụng lại session và token đó khi gửi request đổi mật khẩu hợp lệ.

### 4.1 SQL Injection: `POST /login`

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

### 4.2 Cross-Site Scripting (XSS): `POST /comment`

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

### 4.3 Cross-Site Request Forgery (CSRF): `POST /change-password`

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
    * *Giải thích:* Endpoint không yêu cầu CSRF token, nên một request POST có thể thay đổi mật khẩu.
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

### 4.4 Upload file không an toàn: `POST /upload`

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

## 5. Tổng kết

| Tiêu chí | 🔴 `web_app/` (Vulnerable) | 🟢 `web_app_fixed/` (Fixed) |
| :--- | :--- | :--- |
| **Bản chất** | Mô phỏng thực tế 4 lỗ hổng OWASP Top 10 | Áp dụng các nguyên lý phòng thủ chuẩn |
| **SQLi Protection** | ❌ Không có (Nối chuỗi trực tiếp) | ✅ Có (Parameterized Query `?`) |
| **XSS Protection** | ❌ Không có (Render Raw HTML) | ✅ Có (HTML Escaping `html.escape`) |
| **CSRF Protection** | ❌ Không có | ✅ Có (Synchronizer Token Pattern) |
| **File Upload** | ❌ Không kiểm tra đuôi/tên file | ✅ Whitelist Extension & `secure_filename()` |
| **Kiểm thử thực tế** | Dễ dàng khai thác qua Burp Suite / Postman | Mọi request độc hại đều bị chặn/xử lý an toàn |