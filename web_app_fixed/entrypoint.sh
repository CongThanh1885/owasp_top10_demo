#!/bin/sh
set -e

# Khởi tạo database nếu chưa có
python init_db.py

# Chạy Flask app
python app.py
