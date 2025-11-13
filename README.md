# 🔍 HỆ THỐNG OCR HÓA ĐƠN ĐIỆN & NƯỚC

<div align="center">
<p align="center">
  <img src="img/logoDaiNam.png" alt="DaiNam University Logo" width="200"/>
  <img src="img/LogoAIoTLab.png" alt="AIoTLab Logo" width="170"/>
</p>

[![Made by AIoTLab](https://img.shields.io/badge/Made%20by%20AIoTLab-blue?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Fit DNU](https://img.shields.io/badge/Fit%20DNU-green?style=for-the-badge)](https://fitdnu.net/)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-red?style=for-the-badge)](https://dainam.edu.vn)

</div>

<h2 align="center">Giới thiệu hệ thống</h2>

<p align="left">
  Hệ thống OCR (Optical Character Recognition) hóa đơn điện và nước tự động giúp số hóa và quản lý hóa đơn một cách thông minh. Dự án kết hợp công nghệ xử lý ảnh (OpenCV), nhận dạng ký tự (Tesseract OCR), và fuzzy matching để trích xuất thông tin từ hóa đơn giấy, lưu trữ vào cơ sở dữ liệu MongoDB và xuất kết quả dưới dạng file Excel.
</p>

---

## 🌟 Tính năng chính

- **📸 Upload & OCR tự động:** Upload ảnh hóa đơn, hệ thống tự động xử lý và trích xuất thông tin.
- **🔍 Fuzzy Matching:** Cho phép OCR sai chính tả 28% vẫn nhận diện đúng fields (tên khách hàng, mã KH, tổng tiền...).
- **🎯 Multi-level Preprocessing:** 3 cấp độ tiền xử lý ảnh tự động (resize, denoise, deskew, contrast enhancement).
- **✅ Field Validation:** Kiểm tra tính hợp lệ của dữ liệu trích xuất (mã KH, SĐT, số tiền...).
- **💾 MongoDB Storage:** Lưu trữ dữ liệu linh hoạt với GridFS cho file ảnh và Excel.
- **📊 Export Excel:** Tự động tạo file Excel chứa toàn bộ thông tin đã trích xuất.
- **📈 Dashboard & Statistics:** Giao diện web hiển thị lịch sử xử lý và thống kê.

┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              (Web Browser - HTML/CSS/JS)                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  FLASK API SERVER                        │
│  • Upload endpoint     • Query endpoint                  │
│  • CRUD operations     • Statistics                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              OCR PROCESSING PIPELINE                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 1. Image     │→ │ 2. Tesseract │→ │ 3. Text      │ │
│  │   Preprocess │  │    OCR       │  │   Correction │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│         SMART FIELD EXTRACTION ENGINE                    │
│  • Fuzzy Keyword Matching (72% threshold)                │
│  • Multi-Separator Detection (:, |, ;, ., spaces)        │
│  • Field Validation & Post-processing                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   MONGODB DATABASE                       │
│  • Dynamic schema with GridFS                            │
│  • Store images + OCR data + Excel files                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu trúc dự án
```
📦 tesseract-ocr-system
├── 📂 templates/           # Thư mục chứa giao diện web
│   ├── index.html          # Trang chủ với upload interface
│   └── style.css           # File CSS styling
├── 📂 uploads/             # Thư mục lưu file upload tạm thời
├── 📄 app.py               # Flask API server chính
├── 📄 requirements.txt     # Danh sách thư viện Python
├── 📄 index.aff            # Tesseract dictionary file
├── 📄 vietnamese.txt       # Vietnamese word list
└── 📄 README.md            # Tài liệu hướng dẫn
```

---

## 🛠️ CÔNG NGHỆ SỬ DỤNG

<div align="center">

### 🖥️ Backend
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green?style=for-the-badge&logo=mongodb)](https://www.mongodb.com/)
[![Tesseract](https://img.shields.io/badge/Tesseract-5.3-orange?style=for-the-badge)](https://github.com/tesseract-ocr/tesseract)

### 🔬 Computer Vision & NLP
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-blue?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![Pillow](https://img.shields.io/badge/Pillow-Image%20Processing-yellow?style=for-the-badge)](https://pillow.readthedocs.io/)
[![FuzzyWuzzy](https://img.shields.io/badge/FuzzyWuzzy-Fuzzy%20Matching-pu…style=for-the-badge)](https://github.com/seatgeek/fuzzywuzzy)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-blue?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)

### 🎨 Frontend
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)]()
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)]()
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)]()

</div>

---

## 🛠️ Yêu cầu hệ thống

### 💻 Phần mềm
- **🐍 Python 3.8+** (khuyến nghị Python 3.10+)
- **📦 MongoDB 4.4+** (Community Edition)
- **🔤 Tesseract OCR 5.0+** (với Vietnamese language pack)
- **🌐 Web Browser** hiện đại (Chrome, Firefox, Edge)

### 📦 Các thư viện Python cần thiết

Cài đặt tất cả thư viện bằng lệnh:
```bash
pip install -r requirements.txt
```

**Nội dung file `requirements.txt`:**
```
flask==2.3.0
flask-cors==4.0.0
pymongo==4.5.0
pytesseract==0.3.10
opencv-python==4.8.0.74
Pillow==10.0.0
numpy==1.24.3
pandas==2.0.3
openpyxl==3.1.2
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1
```

---

## 🚀 Hướng dẫn cài đặt và chạy

### 1️⃣ **Cài đặt Tesseract OCR**

#### Windows:
```bash
# Download từ: https://github.com/UB-Mannheim/tesseract/wiki
# Cài đặt và thêm vào PATH
# Download Vietnamese language data từ:
# https://github.com/tesseract-ocr/tessdata/blob/main/vie.traineddata
# Copy file vie.traineddata vào: C:\Program Files\Tesseract-OCR\tessdata
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie
```

#### macOS:
```bash
brew install tesseract
brew install tesseract-lang
```

### 2️⃣ **Cài đặt MongoDB**

#### Windows:
```bash
# Download MongoDB Community Edition từ:
# https://www.mongodb.com/try/download/community
# Cài đặt và khởi động MongoDB service
```

#### Linux:
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### 3️⃣ **Clone project và cài đặt dependencies**
```bash
# Clone repository
git clone https://github.com/your-username/tesseract-ocr-system.git
cd tesseract-ocr-system

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 4️⃣ **Cấu hình Tesseract path** (Windows)

Mở file `app.py` và sửa dòng:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 5️⃣ **Khởi động MongoDB**
```bash
# Kiểm tra MongoDB đang chạy
mongosh
# Hoặc
mongo
```

### 6️⃣ **Chạy ứng dụng**
```bash
python app.py
```

Hoặc:
```bash
flask run
```

Truy cập: **http://localhost:5000**

---

## 📊 Luồng xử lý dữ liệu
```
[User Upload Image]
        ↓
[Image Quality Assessment] → Level 1/2/3 Preprocessing
        ↓
[Tesseract OCR] → Multiple configs (psm3, psm4, psm6)
        ↓
[Text Correction] → Fix common OCR errors
        ↓
[Fuzzy Field Extraction]
   ├─ Strategy 1: Colon-based (:)
   ├─ Strategy 2: Multi-separator (|, ;, .)
   └─ Strategy 3: Pattern matching (regex)
        ↓
[Field Validation] → Check data integrity
        ↓
[Post-processing]
   ├─ Fix customer code (I→1, O→0)
   ├─ Clean phone numbers
   └─ Format dates
        ↓
[Save to MongoDB + Generate Excel]
        ↓
[Return JSON Response to Frontend]
```

---

## 🎯 Các trường dữ liệu trích xuất

### Hóa đơn điện (Electric Bill):
- ✅ **Thông tin công ty:** Tên, địa chỉ, SĐT, mã số thuế
- ✅ **Thông tin hóa đơn:** Số HĐ, ngày, ký hiệu
- ✅ **Thông tin khách hàng:** Tên, địa chỉ, mã KH, MST
- ✅ **Tiêu thụ điện:** Chỉ số cũ/mới, điện tiêu thụ (kWh)
- ✅ **Tiền:** Tổng tiền, VAT, thành tiền

### Hóa đơn nước (Water Bill):
- ✅ **Thông tin công ty:** Tên, địa chỉ, SĐT
- ✅ **Thông tin khách hàng:** Tên, mã KH
- ✅ **Tiêu thụ nước:** Chỉ số cũ/mới, lượng nước (m³)
- ✅ **Tiền:** Tổng tiền, VAT

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Trang chủ web interface |
| `POST` | `/upload` | Upload và xử lý hóa đơn |
| `GET` | `/bills` | Lấy danh sách hóa đơn |
| `GET` | `/bill/<id>` | Xem chi tiết hóa đơn |
| `DELETE` | `/bill/<id>` | Xóa hóa đơn |
| `GET` | `/file/<id>` | Download ảnh gốc |
| `GET` | `/excel/<id>` | Download file Excel |
| `GET` | `/stats` | Thống kê hệ thống |

---

## 📈 Đánh giá hiệu năng

| Metrics | Kết quả |
|---------|---------|
| **Field Extraction Rate** | 75-85% |
| **OCR Confidence** | 70-85% |
| **Processing Time** | 3-5 giây/hóa đơn |
| **False Positive Rate** | < 15% |
| **Support Bill Types** | Điện (EVN), Nước (Sawaco) |

---

## 🐛 Xử lý lỗi thường gặp

### Lỗi: `TesseractNotFoundError`
```bash
# Kiểm tra Tesseract đã cài chưa
tesseract --version

# Nếu chưa có, cài đặt lại và cấu hình path trong app.py
```

### Lỗi: `MongoDB connection failed`
```bash
# Kiểm tra MongoDB đang chạy
sudo systemctl status mongodb  # Linux
# Hoặc mở MongoDB Compass (Windows)

# Khởi động MongoDB
sudo systemctl start mongodb
```

### Lỗi: `ModuleNotFoundError: No module named 'fuzzywuzzy'`
```bash
# Cài đặt lại thư viện
pip install fuzzywuzzy python-Levenshtein
```

---

## 🤝 Đóng góp

Dự án được phát triển bởi:

| Họ và Tên | Vai trò |
|-----------|---------|
| **[Nguyễn Ngọc Bảo Long]** | Phát triển toàn bộ hệ thống OCR, thiết kế kiến trúc, implement Fuzzy Matching, training & testing, biên soạn tài liệu |
| **[Vũ Khánh Hoàn]** | Phát triển toàn bộ hệ thống OCR, thiết kế kiến trúc, implement Fuzzy Matching, training & testing, biên soạn tài liệu |

**Giảng viên hướng dẫn:** Nguyễn Thái Khánh , Lê Trung Hiếu

---

## 📄 License

© 2025 [Nhóm 5], [CNTT 16-02], TRƯỜNG ĐẠI HỌC ĐẠI NAM

---



