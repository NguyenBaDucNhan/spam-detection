# Đọc tin nhắn từ ảnh (OCR)

Tính năng dùng **Tesseract 5**, chạy trên máy đang mở ứng dụng. Không API key, không gửi ảnh tới dịch vụ OCR bên ngoài. Hai bộ nhận dạng **tiếng Việt (`vie`) và tiếng Anh (`eng`)** đã có trong `models/ocr/`; vẫn cần cài chương trình Tesseract riêng.

## Windows

1. Mở trang cài đặt được tài liệu Tesseract giới thiệu: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài Tesseract 5 bản 64-bit. Nếu dùng vị trí thông thường `C:\Program Files\Tesseract-OCR\tesseract.exe`, ứng dụng sẽ tự tìm thấy. Không cần tải thêm ngôn ngữ trong trình cài vì project đã kèm dữ liệu Việt–Anh.
3. Giải nén toàn bộ project, chạy `run_windows.bat` như trước.
4. Trong giao diện mở **Đọc tin nhắn từ ảnh**, tải ảnh và bấm **Trích xuất chữ từ ảnh**.
5. Đọc và sửa văn bản trong ô **Nội dung tin nhắn**, sau đó bấm **Kiểm tra tin nhắn**. OCR không tự chạy phân loại.

Nếu cài Tesseract ở vị trí khác, mở PowerShell tại thư mục project và chạy (đổi đường dẫn cho đúng):

```powershell
$env:TESSERACT_CMD = 'D:\Apps\Tesseract-OCR\tesseract.exe'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Biến môi trường này chỉ áp dụng cho terminal hiện tại. Có thể thêm thư mục Tesseract vào PATH rồi mở terminal mới thay thế. Nếu chưa cài Tesseract, phần nhập tin nhắn thủ công vẫn hoạt động.

## Ubuntu / Debian

```bash
sudo apt-get install tesseract-ocr
```

## macOS (Homebrew)

```bash
brew install tesseract
```

Sau đó cài `requirements.txt` và chạy ứng dụng theo README. Đường dẫn project có dấu cách được truyền an toàn qua danh sách đối số, không cần sửa code.

## Ảnh thử và giới hạn

- Có sẵn `examples/ocr_demo_vi.png` để thử quy trình tiếng Việt; đây là ảnh thử nhân tạo, không phải benchmark độ chính xác thực tế.
- Chọn PNG/JPG/WebP, tối đa 8 MB, 16 triệu điểm ảnh. Không hỗ trợ PDF trong bản này.
- Hệ thống xoay theo EXIF, làm nền trắng cho ảnh trong suốt, chuẩn hóa kích thước/độ tương phản và thử đảo nền tối. Các bước này không đảm bảo đọc đúng mọi giao diện.
- OCR dùng chế độ một khối văn bản. Hãy cắt vùng tin nhắn để tránh lấy cả giờ, tên người gửi, nút bấm hoặc các cuộc trò chuyện khác. Chưa có công cụ cắt ảnh ngay trong giao diện.
- Ảnh mờ, chữ nhỏ, nhiều cột, emoji, font lạ hoặc nền phức tạp có thể bị đọc sai. Cần kiểm tra URL, số tiền, số điện thoại và dấu tiếng Việt trước khi phân loại.
- Giới hạn OCR khoảng 30 giây/lần. Nếu quá thời gian, thử ảnh nhỏ hơn. Văn bản vượt 20.000 ký tự không được điền tự động; hãy cắt vùng nội dung.
- Code không lưu ảnh vào database/file project. Văn bản sau khi sửa được lưu khi bấm phân loại nếu công tắc **Lưu lịch sử kiểm tra trên máy** đang bật. Dữ liệu phản hồi quản lý riêng bằng checkbox đồng ý lưu nội dung. Xem HISTORY_SETUP.md.
- Không hiển thị “% chính xác OCR” vì chưa có tập kiểm tra đại diện. Kết quả OCR có thể ảnh hưởng chất lượng phân loại spam.

## Nguồn và giấy phép

- Tài liệu cài Tesseract: https://tesseract-ocr.github.io/tessdoc/Installation.html
- Dữ liệu nhận dạng: https://github.com/tesseract-ocr/tessdata_fast
- `eng.traineddata` và `vie.traineddata` được lấy từ repository trên khi tạo bản cập nhật; mã băm nằm trong `models/ocr/SOURCES.json`. Giấy phép Apache 2.0 kèm tại `models/ocr/LICENSE`.
- Chương trình Tesseract không được đóng gói trong ZIP; người dùng cài riêng.
