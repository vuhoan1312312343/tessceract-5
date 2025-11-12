# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, make_response
from pymongo import MongoClient
import gridfs
import pytesseract
from PIL import Image, ImageEnhance
from bson.objectid import ObjectId
from datetime import datetime
import pandas as pd
import io
import re
import cv2
import numpy as np
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple
import traceback

app = Flask(__name__)

MONGODB_URI = 'mongodb://localhost:27017/'
DATABASE_NAME = 'bill_ocr_db'

try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    fs = gridfs.GridFS(db)
    # Test connection
    client.server_info()
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Điều chỉnh đường dẫn nếu khác
@dataclass
class BillData:
    # Metadata
    bill_type: str  # 'electric' hoặc 'water'
    confidence_score: float  # 0.0 - 1.0
    preprocessing_level: int  # 1, 2, hoặc 3
    ocr_config_used: str  # psm6, psm4, psm3
    
    # Thông tin công ty
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_tax_code: Optional[str] = None
    company_bank_account: Optional[str] = None
    
    # Thông tin hóa đơn
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_symbol: Optional[str] = None
    
    # Thông tin khách hàng
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_code: Optional[str] = None
    customer_tax_code: Optional[str] = None
    
    # Thông tin tiêu thụ
    reading_period: Optional[str] = None
    old_reading: Optional[str] = None
    new_reading: Optional[str] = None
    usage: Optional[str] = None
    unit: Optional[str] = None  # kWh, m3
    
    # Tiền
    subtotal: Optional[str] = None
    vat_rate: Optional[str] = None
    vat_amount: Optional[str] = None
    env_fee: Optional[str] = None
    total_amount: Optional[str] = None
    total_in_words: Optional[str] = None
    
    # Thanh toán
    payment_method: Optional[str] = None
    payment_due_date: Optional[str] = None
    currency: Optional[str] = None
    
    # Raw data
    ocr_raw_text: Optional[str] = None
    ocr_corrected_text: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

class ImagePreprocessor:
    @staticmethod
    def assess_image_quality(image: np.ndarray) -> Tuple[float, str]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Tính độ sắc nét (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Phân loại
        if laplacian_var > 500:
            return laplacian_var, "Excellent (Clear and sharp)"
        elif laplacian_var > 200:
            return laplacian_var, "Good (Minor blur)"
        elif laplacian_var > 100:
            return laplacian_var, "Fair (Noticeable blur)"
        else:
            return laplacian_var, "Poor (Very blurry)"
    
    @staticmethod
    def preprocess_level_1(image: np.ndarray) -> Image.Image:
        """Level 1: Xử lý cơ bản - cho ảnh chất lượng tốt"""
        print("    Using Level 1 preprocessing (light)")
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binary)
    
    @staticmethod
    def preprocess_level_2(image: np.ndarray) -> Image.Image:
        """Level 2: Xử lý nâng cao - cho ảnh chất lượng trung bình"""
        print("    Using Level 2 preprocessing (medium)")
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(denoised)
        binary = cv2.adaptiveThreshold(contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        pil_image = Image.fromarray(binary)
        return ImageEnhance.Sharpness(pil_image).enhance(1.5)
    
    @staticmethod
    def preprocess_level_3(image: np.ndarray) -> Image.Image:
        """Level 3: Xử lý tối đa - cho ảnh chất lượng kém"""
        print("    Using Level 3 preprocessing (aggressive)")
        image = cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=15)
        kernel = np.ones((2,2), np.uint8)
        morph = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        contrast = clahe.apply(morph)
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            angle = -(90 + angle) if angle < -45 else -angle
            if abs(angle) > 0.5:
                h, w = binary.shape[:2]
                M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                binary = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, 
                                       borderMode=cv2.BORDER_REPLICATE)
        
        return ImageEnhance.Sharpness(Image.fromarray(binary)).enhance(2.0)
    
    @classmethod
    def preprocess_auto(cls, image_bytes: bytes) -> Tuple[Image.Image, int, str]:
        """Tự động chọn level xử lý phù hợp - Returns: (processed_image, level_used, quality_description)"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        quality_score, quality_desc = cls.assess_image_quality(image)
        print(f"    Image quality: {quality_score:.2f} - {quality_desc}")
        
        if quality_score > 500:
            return cls.preprocess_level_1(image), 1, quality_desc
        elif quality_score > 100:
            return cls.preprocess_level_2(image), 2, quality_desc
        else:
            return cls.preprocess_level_3(image), 3, quality_desc

# ============================================================================
# OCR ENGINE
# ============================================================================

class OCREngine:
    """OCR với nhiều config và chọn kết quả tốt nhất"""
    
    CONFIGS = [
        ('psm6', '--oem 3 --psm 6 -c preserve_interword_spaces=1'),
        ('psm4', '--oem 3 --psm 4 -c preserve_interword_spaces=1'),
        ('psm3', '--oem 3 --psm 3'),
    ]
    
    @classmethod
    def run_ocr(cls, image: Image.Image) -> Tuple[str, str, float]:
        """Chạy OCR với nhiều config, chọn kết quả tốt nhất - Returns: (best_text, config_name, confidence)"""
        results = []
        for config_name, config_str in cls.CONFIGS:
            try:
                text = pytesseract.image_to_string(image, lang='vie', config=config_str)
                confidence = cls.estimate_confidence(text)
                results.append((text, config_name, confidence))
                print(f"      Config {config_name}: {len(text)} chars, confidence {confidence:.2f}")
            except Exception as e:
                print(f"      Config {config_name} failed: {e}")
        
        if results:
            best = max(results, key=lambda x: x[2])
            print(f"      → Best: {best[1]} with confidence {best[2]:.2f}")
            return best
        return "", "none", 0.0
    
    @staticmethod
    def estimate_confidence(text: str) -> float:
        """Ước lượng độ tin cậy của OCR result"""
        if not text or len(text) < 10:
            return 0.0
        
        words = text.split()
        if len(words) < 5:
            return 0.2
        
        # Đếm ký tự
        alpha_count = sum(c.isalpha() for c in text)
        digit_count = sum(c.isdigit() for c in text)
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return 0.0
        
        valid_ratio = (alpha_count + digit_count) / total_chars
        word_factor = min(len(words) / 50, 1.0)
        
        return valid_ratio * 0.7 + word_factor * 0.3

# ============================================================================
# TEXT CORRECTOR
# ============================================================================

class TextCorrector:
    """Sửa lỗi OCR cho tiếng Việt"""
    
    COMMON_ERRORS = {
        'công dà': 'công ty', 'drà lệ': 'điện lực', 'ccai giả': 'cầu giấy',
        'cai giay': 'cầu giấy', 'ccông': 'công', 'hoa don': 'hóa đơn',
        'hoá đơn': 'hóa đơn', 'dia chi': 'địa chỉ', 'dien thoai': 'điện thoại',
        'phose': 'phone', 'ma so thue': 'mã số thuế', 'khach hang': 'khách hàng',
        'khách răng': 'khách hàng', 'tong cong': 'tổng cộng', 'thanh toan': 'thanh toán',
        'qhanh hên': 'thanh toán', 'tieu thu': 'tiêu thụ', 'chi so': 'chỉ số',
        'don gia': 'đơn giá', 'thanh tien': 'thành tiền', '4': 'số', 'răng': 'hàng',
        '6': 'số', 's6': 'số', 'l': 'i', 'lI': 'II',
    }
    
    @classmethod
    def correct(cls, text: str) -> str:
        """Sửa lỗi OCR"""
        if not text:
            return text
        
        for wrong, correct in cls.COMMON_ERRORS.items():
            text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text

# ============================================================================
# FIELD EXTRACTOR
# ============================================================================

class FieldExtractor:
    PATTERNS = {
        'electric': {
            # ============= CÔNG TY ĐIỆN LỰC =============
            'company_name': [
                r'CÔNG\s*TY\s*ĐIỆN\s*LỰC\s+([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ\s]+?)(?=\n|Mã)',
                r'CÔNG.*?ĐIỆN.*?LỰC\s+([^\n]+?)(?=\n|Mã)',
            ],
            'company_tax_code': [
                # Dựa vào "Mã số thuế" tiếng Việt, bỏ qua phần tiếng Anh
                r'Mã\s*số\s*thuế[^\d]{0,50}(\d{10,13}[-\d]*)',
                r'(?:Tax|Ta:?)[^\d]{0,30}(\d{10,13}[-\d]*)',
            ],
            'company_address': [
                # Lấy địa chỉ đầu tiên (của công ty điện lực)
                r'Địa\s*chỉ[^\n:]{0,30}:\s*([^\n]+?)(?=\n.*?(?:Điện|EVN|Thông))',
                r'(?:Address|44đ)[^\n:]{0,30}:\s*([^\n]+?)(?=\n)',
            ],
            'company_phone': [
                # Tìm số điện thoại gần "Điện thoại"
                r'Điện\s*th[oe][aả][iị][^\d]{0,30}(\d{7,11})',
                r'(?:Phone|Phoae)[^\d]{0,30}(\d{7,11})',
            ],
            'company_bank_account': [
                r'Số\s*TK\s*[:\s]*(\d{10,20})',
                r'TK\s*[:\s]*(\d{10,20})',
            ],
            
            # ============= HÓA ĐƠN =============
            'invoice_symbol': [
                r'Ký\s*hiệu[^\w]{0,30}(\w+)',
                r'(?:Serial|Szziab)[^\w]{0,30}(\w+)',
            ],
            'invoice_number': [
                r'Số\s*\([Nn]o[^\)]*\)\s*[:\s]*(\d+)',
                r'(?:Số|S)(?:\s*\()?[Nn]o[^\d]{0,20}(\d+)',
            ],
            'invoice_date': [
                r'Ngày[^\d]{0,30}(\d{2}\s*tháng[^\d]{0,30}\d{1,2}\s*năm[^\d]{0,30}\d{4})',
                r'(?:Date|Dakc)[^\d]{0,30}(\d{2}[^\d]{0,30}\d{1,2}[^\d]{0,30}\d{4})',
            ],
            
            # ============= KHÁCH HÀNG =============
            'customer_name': [
                # Dựa vào "Tên đơn vị" tiếng Việt
                r'Tên\s*đơn\s*vị[^\n:]{0,50}:\s*([^\n|]+?)(?=\s*\||Mã\s*số)',
                r'T[âa]n\s*đ[ơo]n\s*v[ịi][^\n:]{0,50}:\s*([^\n|]+?)(?=\s*\||Mã)',
            ],
            'customer_tax_code': [
                # Mã số thuế thứ 2 (của khách hàng)
                # Tìm sau "Tên đơn vị"
                r'Tên\s*đơn\s*vị[^\n]+\n.*?Mã\s*số\s*thuế[^\d]{0,50}(\d{10,13})',
                r'(?:Company|Cowpony)[^\n]+\n.*?(?:Tax|thuế)[^\d]{0,50}(\d{10,13})',
            ],
            'customer_address': [
                # Địa chỉ thứ 2 (của khách hàng) - sau customer name
                r'Tên\s*đơn\s*vị[^\n]+\n[^\n]+\n.*?Địa\s*chỉ[^\n:]{0,30}:\s*([^\n]+?)(?=Mã\s*khách)',
            ],
            'customer_code': [
                r'Mã\s*khách\s*hàng[^\w]{0,50}([\w\d]{5,20})',
                r'(?:Customer|Cxtioser)[^\w]{0,50}([\w\d]{5,20})',
            ],
            'payment_method': [
                r'Hình\s*thức\s*thanh\s*to[áa]n[^\n:]{0,30}:\s*([^\n,]+?)(?=\n|Đồng)',
                r'(?:Payment|Payaes)[^\n:]{0,30}:\s*([^\n,]+)',
            ],
            'currency': [
                r'Đồng\s*tiền[^\n:]{0,30}:\s*(VN[DĐ]|USD)',
                r'(?:currency|cưreaey)[^\n:]{0,30}:\s*(VN[DĐ]|USD)',
            ],
            
            # ============= TIÊU THỤ =============
            'reading_period': [
                r'từ\s*ngày\s*[/\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\s*đến\s*ngày\s*[/\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'tháng\s*(\d{1,2})\s*năm\s*(\d{4})',
            ],
            'usage': [
                # Tìm số gần "kWh"
                r'kWh[^\d]{0,30}(\d+)',
                r'(\d{2,4})\s*kWh',
            ],
            
            # ============= TIỀN =============
            'subtotal': [
                r'Cộng\s*tiền\s*hàng[^\d]{0,50}([\d\.,]+)',
                r'(?:Total|tmuóm)[^\d]{0,50}([\d\.,]+)',
            ],
            'vat_rate': [
                r'Thuế\s*suất[^\d]{0,30}(\d+)\s*%',
                r'VAT[^\d]{0,30}(\d+)\s*%',
            ],
            'vat_amount': [
                r'Tiền\s*thuế\s*GTGT[^\d]{0,50}([\d\.,]+)',
                r'VAT[^\d]{0,30}([\d\.,]+)(?!\s*%)',
            ],
            'total_amount': [
                r'Tổng\s*cộng\s*tiền\s*thanh\s*toán[^\d]{0,50}([\d\.,]+)',
                r'(?:Total|Tổng)[^\d]{0,30}([\d\.,]+)',
            ],
            'total_in_words': [
                r'Số\s*tiền\s*bằng\s*chữ[^\n:]{0,30}:\s*([^\n]+?)(?=\s*Người)',
                r'(?:Amount|4meown)[^\n:]{0,30}:\s*([^\n]+?)(?=\s*Người)',
            ],
        },
        
        'water': {
            'company_name': [
                r'(CÔNG\s*TY[^\n]*?NƯỚC[^\n]*?(?=\s*Ký\s*hiệu|\s*Địa\s*chỉ|\n|$))',
            ],
            'company_tax_code': [
                r'Mã\s*(?:số|số\s*thuế)[^\d]{0,10}(\d{10,13})',
            ],
            'company_address': [
                # Cắt từ “Địa chỉ” cho đến trước khi gặp “Số:” hoặc “Mã số thuế” hoặc “HÓA ĐƠN”
                r'Địa\s*chỉ[:\s]*([A-Z0-9].*?)(?=\s*Số[:\s]|Mã\s*số\s*thuế|HÓA\s*ĐƠN|\n|$)',
            ],
            'invoice_symbol': [
                r'Ký\s*hiệu[:\s]*([A-Z0-9]{5,})',
            ],
            'invoice_number': [
                r'Số[:\s]*(\d{6,})',
            ],
            'invoice_date': [
                r'Ngày\s*ký[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
                r'Ngày\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            ],
            'customer_name': [
                r'Tên\s*(?:khách\s*hàng|kh)\s*[:\-\s]*([A-ZÁÀÂÃÄĂẮẰẲẴẶÂÉÈÊẾỀỂỄẸÍÌÎÏÓÒÔÕÖƠÚÙÛÜƯÝỲỶỸỴĐa-zàáâãäăắằẳẵặâéèêếềểễẹíìîïóòôõöơúùûüưýỳỷỹỵđ0-9\s\.\-]{2,120}?)(?=\s*(?:Mã|Địa|Tài|Mã số|Thời|Số|$|\n|,|\.))',
                r'(?:Họ\s*tên|Khách\s*hàng)[:\s]*([A-ZÀÁÂÃÄĂẮẰẲẴẶÂÉÈÊẾỀỂỄẸÍÌÎÏÓÒÔÕÖƠÚÙÛÜƯÝỲỶỸỴĐa-zàáâãäăắằẳẵặâéèêếềểễẹíìîïóòôõöơúùûüưýỳỷỹỵđ\s\.\-]{2,120}?)(?=\s*(?:Mã|Địa|Tài|Mã số|Thời|Số|$|\n|,|\.))',
            ],
            'customer_address': [
                r'Địa\s*chỉ\s*[:\-]?\s*([A-ZÀÁÂÃÄĂẮẰẲẴẶÂÉÈÊẾỀỂỄẸÍÌÎÏÓÒÔÕÖƠÚÙÛÜƯÝỲỶỸỴĐa-zàáâãäăắằẳẵặâéèêếềểễẹíìîïóòôõöơúùûüưýỳỷỹỵđ0-9\s\/\.\,\-\(\)]{2,200}?)(?=\s*(?:Mã|Tài|Thời|Số|Phí|Tổng|$|\n|,|\.))',
                r'(?:Địa\s*điểm|Nơi\s*sử\s*dụng)\s*[:\-]?\s*([A-Z0-9a-zÀ-ỹ\/\s\.,\-]{2,200}?)(?=\s*(?:Mã|Tài|Thời|Số|Phí|Tổng|$|\n|,|\.))',
            ],
            'customer_code': [
                r'Mã\s*(?:số\s*)?khách\s*hàng[:\s]*([0-9A-Z]+)',
            ],
            'old_reading': [
                r'Số\s*Đọc\s*Tháng\s*Trước[^\d]{0,10}(\d+)',
            ],
            'new_reading': [
                r'Số\s*Đọc\s*Tháng\s*Này[^\d]{0,10}(\d+)',
            ],
            'usage': [
                r'Số\s*Lượng\s*Tiêu\s*Thụ[^\d]{0,10}(\d+)',
                r'Tiêu\s*thụ[:\s]*([0-9]+)',
            ],
            'env_fee': [
                r'Phí\s*(?:BVMT|bảo\s*vệ\s*môi\s*trường)[^\d]{0,10}([\d\.]+)',
            ],
            'subtotal': [
                r'Cộng\s*(?:tiền\s*hàng|tiền)[^\d]{0,20}([\d\.,]+)',
            ],
            'vat_rate': [
                r'Thuế\s*Suất[:\s]*(\d+)\s*%',
            ],
            'total_amount': [
                r'Tổng\s*(?:tiền\s*thanh\s*toán|cộng)[^\d]{0,20}([\d\.,]+)',
            ],
            'total_in_words': [
                r'Số\s*tiền\s*bằng\s*chữ[:\s]*([^\n]+)',
            ],
        },


    }
    @classmethod
    def extract(cls, text: str, bill_type: str) -> Dict[str, Optional[str]]:
        """Trích xuất các field từ text"""
        patterns = cls.PATTERNS.get(bill_type, {})
        text_normalized = cls.normalize_text(text)
        return {field: cls.extract_field(text_normalized, pattern_list) 
                for field, pattern_list in patterns.items()}
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Chuẩn hóa text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*:\s*', ': ', text)
        return text
    
    @classmethod
    def extract_field(cls, text, patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    result = match.group(match.lastindex or 1).strip() if match.lastindex else match.group(0).strip()
                    return result
                except IndexError:
                    continue
        return ""



class BillOCRPipeline:
    """Pipeline chính"""
    
    @staticmethod
    def process(image_bytes: bytes, bill_type: str) -> BillData:
        """Xử lý toàn bộ pipeline"""
        print("  [1/5] Preprocessing image...")
        processed_image, level, quality = ImagePreprocessor.preprocess_auto(image_bytes)
        
        print("  [2/5] Running OCR...")
        ocr_text, config_name, ocr_confidence = OCREngine.run_ocr(processed_image)
        print(f"      → Extracted {len(ocr_text)} characters")
        
        print("  [3/5] Correcting text...")
        corrected_text = TextCorrector.correct(ocr_text)
        
        print("  [4/5] Extracting fields...")
        extracted = FieldExtractor.extract(corrected_text, bill_type)
        found_fields = len([v for v in extracted.values() if v])
        print(f"      → Found {found_fields}/{len(extracted)} fields")
        
        print("  [5/5] Building result...")
        return BillData(
            bill_type=bill_type,
            confidence_score=ocr_confidence,
            preprocessing_level=level,
            ocr_config_used=config_name,
            ocr_raw_text=ocr_text[:5000],
            ocr_corrected_text=corrected_text[:5000],
            **extracted
        )

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload và xử lý hóa đơn"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    filename = file.filename
    bill_type = request.form.get('bill_type', 'electric')
    
    if not filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        return jsonify({'error': 'Only image files are supported'}), 400
    
    try:
        print(f"\n{'='*70}")
        print(f"📄 Processing: {filename}")
        print(f"📋 Type: {bill_type.upper()}")
        print(f"{'='*70}")
        
        # Đọc file
        file_bytes = file.read()
        
        # Xử lý OCR
        bill_data = BillOCRPipeline.process(file_bytes, bill_type)
        
        # Lưu file gốc
        file.seek(0)
        file_id = fs.put(file, filename=filename, content_type='image/jpeg')
        
        # Tạo Excel
        df = pd.DataFrame([bill_data.to_dict()])
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bill Data')
        
        excel_buffer.seek(0)
        excel_filename = f"{filename.rsplit('.', 1)[0]}_result.xlsx"
        excel_file_id = fs.put(
            excel_buffer, 
            filename=excel_filename, 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Lưu vào MongoDB
        result = db.bills.insert_one({
            'filename': filename,
            'file_id': file_id,
            'excel_file_id': excel_file_id,
            'upload_date': datetime.now(),
            'bill_type': bill_type,
            'confidence_score': bill_data.confidence_score,
            'preprocessing_level': bill_data.preprocessing_level,
            'ocr_config_used': bill_data.ocr_config_used,
            'data': bill_data.to_dict()
        })
        
        print(f"✅ Success! Saved with ID: {result.inserted_id}")
        print(f"   Confidence: {bill_data.confidence_score:.2%}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'message': 'Bill processed successfully',
            'bill_id': str(result.inserted_id),
            'confidence': round(bill_data.confidence_score, 2),
            'data': bill_data.to_dict(),
            'excel_id': str(excel_file_id)
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/bills', methods=['GET'])
def list_bills():
    """Lấy danh sách hóa đơn"""
    try:
        bills = db.bills.find().sort('upload_date', -1).limit(100)
        return jsonify({
            'success': True,
            'bills': [{
                'id': str(b['_id']),
                'filename': b['filename'],
                'bill_type': b['bill_type'],
                'confidence': round(b.get('confidence_score', 0), 2),
                'upload_date': b['upload_date'].strftime('%Y-%m-%d %H:%M:%S'),
                'customer_name': b['data'].get('customer_name', 'N/A'),
                'total_amount': b['data'].get('total_amount', 'N/A'),
                'invoice_number': b['data'].get('invoice_number', 'N/A'),
                'excel_id': str(b.get('excel_file_id')) if b.get('excel_file_id') else None
            } for b in bills]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bill/<id>', methods=['GET'])
def get_bill(id):
    """Lấy chi tiết hóa đơn"""
    try:
        bill = db.bills.find_one({'_id': ObjectId(id)})
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        
        bill['_id'] = str(bill['_id'])
        bill['file_id'] = str(bill['file_id'])
        if bill.get('excel_file_id'):
            bill['excel_file_id'] = str(bill['excel_file_id'])
        return jsonify({'success': True, 'bill': bill})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bill/<id>', methods=['DELETE'])
def delete_bill(id):
    """Xóa hóa đơn"""
    try:
        bill = db.bills.find_one({'_id': ObjectId(id)})
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        
        if bill.get('file_id'):
            fs.delete(bill['file_id'])
        if bill.get('excel_file_id'):
            fs.delete(bill['excel_file_id'])
        
        db.bills.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': True, 'message': 'Bill deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/file/<id>', methods=['GET'])
def get_file(id):
    """Download file ảnh gốc"""
    try:
        file = fs.get(ObjectId(id))
        response = make_response(file.read())
        response.headers['Content-Type'] = file.content_type or 'image/jpeg'
        response.headers['Content-Disposition'] = f'inline; filename={file.filename}'
        return response
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@app.route('/excel/<id>', methods=['GET'])
def get_excel(id):
    """Download Excel result"""
    try:
        file = fs.get(ObjectId(id))
        response = make_response(file.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={file.filename}'
        return response
    except Exception as e:
        return jsonify({'error': 'Excel file not found'}), 404

@app.route('/stats', methods=['GET'])
def get_stats():
    """Thống kê hệ thống"""
    try:
        avg_result = list(db.bills.aggregate([{'$group': {'_id': None, 'avg_confidence': {'$avg': '$confidence_score'}}}]))
        avg_confidence = avg_result[0]['avg_confidence'] if avg_result else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_bills': db.bills.count_documents({}),
                'electric_bills': db.bills.count_documents({'bill_type': 'electric'}),
                'water_bills': db.bills.count_documents({'bill_type': 'water'}),
                'avg_confidence': round(avg_confidence, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)