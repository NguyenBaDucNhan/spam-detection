# Trợ lý kiểm tra tin nhắn spam

Bản chạy thử độc lập từ project gốc: không Gmail, không OAuth, không tài khoản, không cần API key cho phần phân loại/OCR. Tra cứu link trực tuyến là tùy chọn, cần key riêng. Dùng model **TF-IDF ký tự + Linear SVM** Anh–Việt có sẵn, giữ nguyên file model. Chạy trên máy cá nhân; cần Internet lần đầu để cài thư viện.

Muốn hiểu hoặc sửa code: đọc [CODE_GUIDE.md](CODE_GUIDE.md). File này mô tả thứ tự đọc code và đầu ra của các hàm chính.

## 1. Chạy nhanh trên Windows

Cài **Python 3.12 64-bit** (khuyên dùng; thư viện yêu cầu Python >=3.11). Giải nén ZIP, mở thư mục `spam_detection` có file `app.py`.

**Cách thuận tiện:** bấm đúp `run_windows.bat`. Script tạo môi trường `.venv`, cài thư viện và mở Streamlit. Nếu lệnh `py -3.12` không tồn tại, dùng cách bên dưới với Python >=3.11 đã cài.

**Hoặc mở PowerShell / terminal VS Code tại thư mục project:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở địa chỉ **http://localhost:8501** nếu trình duyệt chưa tự mở. Nhấn `Ctrl+C` trong terminal để dừng. Lần sau chỉ cần chạy lệnh Streamlit cuối cùng. Không cần activate môi trường nên không phải thay đổi PowerShell execution policy.

## 2. macOS / Linux

Tại thư mục project, với Python >=3.11:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Hoặc dùng `bash run.sh`.

## 3. Sử dụng

1. Nhập tin nhắn hoặc đường link cần kiểm tra.
2. Bấm **Kiểm tra tin nhắn** để xem dự đoán spam/không spam.
3. Có thể mở **Đọc tin nhắn từ ảnh**, tải ảnh và trích xuất chữ, sửa văn bản rồi kiểm tra. Cài Tesseract 5 theo [OCR_SETUP.md](OCR_SETUP.md) để dùng tính năng này.
4. Xem dấu hiệu: có đường link, OTP, lời thúc giục, yêu cầu chuyển tiền, nhận thưởng.
5. Gửi nhãn bạn cho là đúng nếu muốn góp ý.

**Phân biệt hai phần:** dự đoán do SVM đưa ra; dấu hiệu do các quy tắc riêng tìm thấy. Quy tắc không giải thích trực tiếp quyết định của SVM. Nhắc đến OTP hoặc có link không đồng nghĩa với spam. Ứng dụng phân tích cấu trúc URL trên máy và có nút tra cứu Google Safe Browsing khi cấu hình key; không mở website đích. Xem [LINK_SETUP.md](LINK_SETUP.md). Nhãn “không spam” không chứng minh tin nhắn an toàn.

Điểm quyết định trong mục kỹ thuật là khoảng cách có dấu của SVM, **không phải xác suất / phần trăm độ tin cậy**. Với hai lớp của model này, điểm dương nghiêng về spam, điểm âm nghiêng về ham.

### Phản hồi và dữ liệu

- Chỉ khi bấm gửi phản hồi mới ghi vào `data/feedback.sqlite3`, trên máy đang chạy ứng dụng.
- Trong file phản hồi, mặc định chỉ ghi UUID, thời gian, mã model, nhãn dự đoán, nhãn phản hồi và điểm SVM.
- File phản hồi chỉ ghi nội dung khi tích đồng ý. Lịch sử kiểm tra lưu riêng theo công tắc ngay dưới ô nhập nội dung; tắt công tắc trước khi kiểm tra nội dung riêng tư.
- **Lịch sử kiểm tra:** mặc định bật, lưu nội dung, kết quả và thời gian vào `data/history.sqlite3`. Xem lại ở cuối trang; có tìm kiếm, lọc, phân trang và xóa. Chưa có đăng nhập nên đây là lịch sử chung của bản chạy, không tách riêng từng tài khoản. Xem [HISTORY_SETUP.md](HISTORY_SETUP.md).
- Phản hồi **không tự động huấn luyện model**. Cần kiểm duyệt nhãn trước khi sử dụng.
- Dừng ứng dụng rồi xóa `data/feedback.sqlite3` nếu muốn xóa toàn bộ phản hồi.

## 4. Cấu trúc và luồng chạy

```text
spam_detection/
├── app.py                    # Giao diện Streamlit
├── src/
│   ├── __init__.py
│   ├── settings.py           # Cấu hình và đường dẫn theo gốc project
│   ├── preprocessing.py      # Làm sạch, kiểm tra văn bản
│   ├── dataset.py            # Đọc, chuẩn hóa, loại trùng và chia dữ liệu
│   ├── train.py              # Một điểm chạy huấn luyện
│   ├── evaluate.py           # Đánh giá và lưu metrics
│   ├── predictor.py          # Nạp model, dự đoán cho cả UI và CLI
│   ├── link_check.py         # Phân tích URL và tra cứu Safe Browsing theo yêu cầu
│   ├── ocr.py                # Trích xuất chữ bằng Tesseract trên máy
│   ├── indicators.py         # Các dấu hiệu theo quy tắc, không gọi mạng
│   ├── history.py            # Lưu và truy vấn lịch sử SQLite
│   ├── history_ui.py         # Xem, lọc, tìm và xóa lịch sử
│   └── feedback.py           # SQLite, nội dung tùy chọn
├── configs/app.json
├── data/                     # Ba CSV gốc, SQLite lịch sử/phản hồi khi sử dụng
├── models/                   # Model có sẵn và thông tin nguồn gốc
├── reports/                  # Báo cáo cũ và báo cáo kiểm thử bản này
├── tests/                    # unittest + Streamlit AppTest
├── requirements.txt
├── run_windows.bat
├── run.sh
├── HISTORY_SETUP.md          # Lưu lịch sử và giới hạn bản chưa đăng nhập
├── LINK_SETUP.md             # Cấu hình API key và giới hạn kiểm tra link
├── OCR_SETUP.md              # Cài đặt OCR
├── examples/ocr_demo_vi.png   # Ảnh thử tiếng Việt
└── README.md
```

Luồng dự đoán: `app.py` hoặc CLI → `SpamPredictor` → chuẩn hóa → pipeline TF-IDF/SVM. Song song, `indicators.py` tìm dấu hiệu. Chỉ thao tác gửi phản hồi mới gọi `feedback.py`. Mở ứng dụng không chạy huấn luyện.

## 5. Chạy terminal, kiểm thử

Các lệnh sau dùng `python` của môi trường đã cài requirements. Trên Windows có thể thay `python` bằng `.\.venv\Scripts\python.exe`; macOS/Linux bằng `.venv/bin/python`.

```bash
python -m src.predictor "Mai mình gặp nhau lúc 8 giờ nhé"
python -m unittest discover -s tests -v
```

Chạy các lệnh module từ thư mục gốc project. Đường dẫn model, cấu hình, dữ liệu và phản hồi được neo vào gốc project, không dựa vào thư mục làm việc của Streamlit.

## 6. Huấn luyện lại

Không cần huấn luyện để chạy thử. Khi cần:

```bash
# Chỉ SMS Anh + Việt: phù hợp phạm vi SMS
python -m src.train --sources sms_en sms_vi

# Hoặc chỉ tiếng Việt
python -m src.train --sources sms_vi --output models/spam_vi.pkl

# Không truyền sources: gồm SMS Anh, SMS Việt và email Việt tổng hợp
python -m src.train
```

Mặc định lưu **model mới** vào `models/spam_retrained.pkl`; giữ nguyên model đóng gói. Để sử dụng model mới, đổi `model_path` trong `configs/app.json` rồi khởi động lại app. File `.metrics.json` cạnh model lưu kết quả của chính lần huấn luyện đó. Các dự đoán test và lỗi nằm ở `reports/<tên_model>/`.

Tiền xử lý giữ tương thích với model gốc: chuyển chữ thường, gộp khoảng trắng, bỏ khoảng trắng đầu/cuối. Loại nội dung rỗng, nhãn mâu thuẫn và trùng hoàn toàn trước khi chia. Luồng mới chia theo nhóm câu đã thay URL và token chứa số bằng ký hiệu, giúp hạn chế rò rỉ các câu chỉ khác những thành phần này. Đây là heuristic, **chưa phát hiện mọi câu gần giống hoặc trùng ý nghĩa**. Dùng fold đầu của StratifiedGroupKFold 5 folds làm test, seed 30; tỷ lệ test có thể không đúng 20% do kích thước nhóm.

### Nguồn dữ liệu được giữ lại

| File | Số dòng gốc | Vai trò |
|---|---:|---|
| `spam.csv` | 5.572 | SMS tiếng Anh, nhãn ham/spam |
| `full_dataset.csv` | 2.991 | SMS tiếng Việt, nhãn 0/1 |
| `email_spam_vietnamese.csv` | 3.127 | Email tiếng Việt tổng hợp |

Các file được sao chép nguyên từ project bạn gửi. Chưa kiểm chứng độc lập xuất xứ, chất lượng nhãn hoặc quyền phân phối. Enron và model chỉ tiếng Anh cũ không cần cho bản chạy thử này nên không đóng gói.

`reports/bundled_model_metrics.json` là **báo cáo cũ đi kèm model**, không phải kết quả huấn luyện lại bản này. Báo cáo cũ chia ngẫu nhiên theo nguồn, khác phương pháp chia theo nhóm của luồng mới. Không so sánh trực tiếp hai kết quả như cùng một bài kiểm tra. Email tổng hợp đạt 100% trên holdout không chứng minh chất lượng thực tế.

## 7. Đánh giá bằng dữ liệu mới

Chuẩn bị CSV UTF-8 có cột `label,message`, nhãn `ham/spam` hoặc `0/1`, với nội dung chưa xuất hiện trong dữ liệu huấn luyện:

```bash
python -m src.evaluate --csv duong_dan/tap_doc_lap.csv
python -m src.evaluate --csv duong_dan/tap_doc_lap.csv --model models/spam_vi.pkl
```

Báo cáo mặc định: `reports/independent_evaluation.json`, gồm accuracy, precision/recall/F1 spam, số báo nhầm, số bỏ sót và confusion matrix (thứ tự ham, spam). Công cụ không tự xác minh dữ liệu đầu vào có độc lập hay không.

## 8. Lỗi thường gặp và phạm vi bản này

- `No module named ...`: cài requirements bằng đúng Python dùng để chạy app.
- Không tạo được môi trường: kiểm tra Python >=3.11; Python 3.12 được khuyên dùng.
- Không nạp được model: giữ đủ thư mục `models/`, cài đúng `scikit-learn==1.8.0`. Chỉ nạp pickle do bạn tin cậy.
- Không lưu được phản hồi: kiểm tra quyền ghi thư mục `data/`.
- Bản này có OCR Việt–Anh chạy bằng Tesseract 5; có phân tích URL và tra cứu Google Safe Browsing tùy chọn; chưa có tài khoản hay tích hợp nền tảng nhắn tin. Các mục này là bước mở rộng sau khi kiểm chứng luồng dùng cơ bản.

## 9. OCR: ảnh → văn bản → phân loại

Mở mục **Đọc tin nhắn từ ảnh**, chọn ảnh, bấm **Trích xuất chữ từ ảnh**, xem/sửa nội dung rồi bấm **Kiểm tra tin nhắn**. Cần cài Tesseract 5 riêng; hướng dẫn đầy đủ tại [OCR_SETUP.md](OCR_SETUP.md). Bộ nhận dạng Việt–Anh đã đi kèm project. Không có Tesseract vẫn dùng được phần nhập văn bản.

## 10. Kiểm tra đường link

Dán một URL hoặc tin nhắn có link vào ô nội dung. Mục **Kiểm tra đường link** hiển thị các dấu hiệu cấu trúc ngay trên máy. Để tra cứu trực tuyến, nhập API key vào mục thiết lập rồi bấm **Tra cứu link N**. Mỗi lần bấm gửi URL chuẩn hóa đó tới Google, không gửi toàn bộ tin nhắn. Không tìm thấy cảnh báo không đảm bảo an toàn. Hướng dẫn tạo key, sử dụng phi thương mại, giới hạn và cách đọc kết quả tại [LINK_SETUP.md](LINK_SETUP.md). Không có key vẫn dùng được các chức năng còn lại.

## 11. Lịch sử kiểm tra

Công tắc **Lưu lịch sử kiểm tra trên máy** ngay dưới ô nhập nội dung mặc định bật. Sau khi phân loại tin nhắn hoặc tra cứu link, mở **Lịch sử kiểm tra** ở cuối trang để xem lại, tìm, lọc và xóa. Dữ liệu tồn tại sau khi khởi động lại nếu giữ `data/history.sqlite3`. Chưa có xác thực: mọi người mở cùng bản chạy app xem chung lịch sử. Tắt công tắc trước khi kiểm tra dữ liệu riêng tư. Chi tiết và cách giữ dữ liệu khi nâng cấp: [HISTORY_SETUP.md](HISTORY_SETUP.md).
