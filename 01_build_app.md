# Giai đoạn 1: Xây dựng web app cơ bản

## Mục tiêu
- Tạo ứng dụng web nhỏ (Flask/Django hoặc Node.js).
- Chức năng: đăng nhập, form comment, upload file, đổi mật khẩu.
- Cố tình chèn lỗ hổng OWASP Top 10.

## Lỗ hổng cần thêm
- SQL Injection: form login.
- XSS: form comment.
- CSRF: chức năng đổi mật khẩu.
- Insecure File Upload: upload ảnh.

## Kết quả
- App chạy được trên localhost.
- Có thể deploy bằng Docker để dễ quản lý.
