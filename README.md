# 🌟 Hệ Thống Tạo Thiệp Chúc Mừng AI

Hệ thống AI tự động tạo thiệp chúc mừng với giao diện thân thiện, hỗ trợ nhiều loại thiệp và tùy chỉnh nội dung theo yêu cầu.

## ✨ Tính Năng

### 🎨 Tạo Thiệp Tự Động
- **AI Generation**: Sử dụng LLM để tạo nội dung thiệp phù hợp
- **Template có sẵn**: Hơn 13 loại thiệp khác nhau (sinh nhật, Giáng sinh, tốt nghiệp, v.v.)
- **Tùy chỉnh aspect ratio**: Hỗ trợ tỉ lệ 3:4 và 4:3

### 🖼️ Xử Lý Hình Ảnh
- **Upload ảnh custom**: Cho phép người dùng tải ảnh riêng
- **Tự động matching**: Tìm background phù hợp với foreground được upload
- **Blending**: Kết hợp hình ảnh người dùng tải lên (foreground) với background với hiệu ứng chuyển màu
- **Dominant color detection**: Phân tích màu chủ đạo để chọn font color
- **Template có sẵn**: Kết hợp foreground và background có sẵn để tạo template

### 🎯 Loại Thiệp Hỗ Trợ
- Sinh nhật (birthday)
- Giáng sinh (christmas)
- Tốt nghiệp (graduation)
- Tết Dương lịch (newyear)
- Tết Nguyên đán (lunar_newyear)
- Tết Trung thu (mid_autumn_festival)
- Lễ tình nhân (valentine)
- Ngày Nhà giáo Việt Nam (vietnam_teacherday)
- Quốc khánh Việt Nam (vietnam_nationalday)
- Ngày Phụ nữ Việt Nam (vietnam_womenday)
- Lễ cưới (wedding)
- Ngày Quốc tế Phụ nữ (international_womenday)
- Thiệp chung (general)

### Cài Đặt Dependencies

```bash
# Clone repository
git clone https://github.com/heidiie13/card_generator.git
cd card_generator

# Tạo môi trường ảo
conda create -n llm python=3.11 -y
conda activate llm

# Cài đặt packages
pip install -r requirements.txt
```

## ⚙️ Cấu Hình

### Tạo File Environment
```bash
cp .env.example .env
```

### Cấu Hình .env
```env
# API Configuration cho LLM
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://your-api-endpoint.com
MODEL_NAME=your_model_name

# Backend URL cho Frontend
BACKEND_URL=http://localhost:8000
```

### Tạo Metadata:
```bash
# Có thể tải mẫu và tạo Metadata qua API
# Hoặc
python utils/metadata.py
```

## 🎯 Sử Dụng

### Khởi Chạy Backend API
```bash
uvicorn api.main:app --reload --port 8000
```

### Khởi Chạy Frontend
```bash
streamlit run app.py
```

### Truy Cập Ứng Dụng
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

### Sử Dụng Cơ Bản

1. **Chọn tỉ lệ khung hình**: 3:4 hoặc 4:3
2. **Nhập yêu cầu nội dung**: Mô tả thiệp bạn muốn tạo (bắt buộc)
3. **Chọn chế độ** (nếu bật tùy chỉnh):
   - **Ngẫu nhiên**: Hệ thống chọn ngẫu nhiên template theo từng loại thiệp
   - **Chọn template**: Chọn template theo từng loại thiệp
   - **Upload ảnh**: Tải ảnh của bạn
4. **Nhấn "Tạo thiệp"**
5. **Tải về kết quả**