# Cách đọc code của project

Bản này viết lại cho dễ đọc, giữ nguyên cách gọi hàm và định dạng kết quả của bản trước. Các biểu thức nhiều bước được tách thành biến trung gian và vòng lặp; chú thích giải thích mục đích của từng bước. Không thay model, CSV, cấu hình, nhãn hoặc giao diện sử dụng.

## Nên đọc theo thứ tự

1. `src/preprocessing.py`: cách kiểm tra đầu vào và làm sạch một chuỗi.
2. `src/predictor.py`: model nhận danh sách văn bản và trả về kết quả dự đoán.
3. `src/indicators.py`: vòng lặp tìm dấu hiệu bằng quy tắc.
4. `app.py`: tám phần được đánh số, từ nạp model đến hiển thị lịch sử.
5. `src/feedback.py`, `src/history.py`: câu lệnh SQLite để lưu/đọc/xóa dữ liệu.
6. `src/link_check.py`, `src/ocr.py`: chuẩn bị dữ liệu, gọi dịch vụ/chương trình, xử lý lỗi.
7. `src/dataset.py`, `src/evaluate.py`, `src/train.py`: chuẩn bị dữ liệu, tính chỉ số và huấn luyện lại.

## Các hàm chính trả về gì?

| Hàm | Kết quả |
|---|---|
| `clean_text(text)` | Chuỗi đã chuyển chữ thường và bỏ khoảng trắng thừa |
| `validate_text(text)` | Chuỗi đã làm sạch; báo ValueError nếu đầu vào không hợp lệ |
| `SpamPredictor.predict(text)` | Đối tượng Prediction gồm label, score, model_id, indicators |
| `Prediction.to_dict()` | Dictionary chứa bốn trường trên |
| `analyze_indicators(text)` | Danh sách dictionary, mỗi dictionary là một dấu hiệu |
| `extract_urls(text)` | Danh sách URL theo thứ tự xuất hiện, không trùng |
| `analyze_url(raw)` | Dictionary gồm original, url, host, warnings, eligible, reason |
| `lookup_url(raw, api_key)` | Dictionary kết quả tra cứu; lỗi báo LinkCheckError |
| `prepare_image(data)` | Ảnh Pillow đã chuẩn hóa |
| `extract_text(data, language)` | OCRResult gồm text, language, width, height |
| `save_feedback(...)`, `save_message(...)`, `save_link(...)` | ID dạng chuỗi của bản ghi vừa lưu |
| `list_history(...)` | Tuple: (danh sách bản ghi của trang, tổng số bản ghi khớp) |
| `delete_history(...)` | Số bản ghi đã xóa |
| `load_dataset(...)`, `read_source(...)` | DataFrame của pandas |
| `split_dataset(df)` | Tuple: (DataFrame train, DataFrame test) |
| `metrics(y_true, y_pred)` | Dictionary các chỉ số đánh giá |

## Các khái niệm vẫn được giữ lại

- **Dictionary**: gom kết quả có tên trường, ví dụ `result['label']`.
- **Dataclass**: giữ nguyên kiểu đối tượng Prediction/OCRResult đang dùng; có thể đọc giá trị bằng `result.label` hoặc `result.text`.
- **`with connect(...)`**: mở kết nối database cho một khối lệnh, tự commit/rollback rồi đóng kết nối.
- **Regex**: tìm mẫu trong văn bản/URL; giữ nguyên các mẫu của bản trước vì thay mẫu có thể đổi kết quả.
- **Pipeline**: giữ TF-IDF và SVM trong cùng một model để dự đoán đúng quy trình đã huấn luyện.
- **`st.session_state`**: giữ dữ liệu trong phiên Streamlit. File app chạy lại sau mỗi tương tác; chỉ ghi lịch sử trong nhánh người dùng bấm nút.

## Kiểm tra đầu ra sau khi sửa

Chạy từ thư mục gốc project:

```bash
python -m unittest discover -s tests -v
```

`tests/fixtures/before_refactor.json` giữ kết quả từ bản trước. `test_regression.py` đối chiếu tham số hàm, dự đoán, điểm SVM, dấu hiệu và lỗi trên các đầu vào cố định. Kiểm tra toàn bộ nhãn/điểm trên dữ liệu gốc dùng mã băm để không lưu một file kết quả quá dài.

Thời gian kiểm tra và ID bản ghi mới vẫn được tạo khi chạy nên đương nhiên khác giữa hai lượt. Khi đối chiếu database và tra cứu mô phỏng trước/sau refactor, thời gian và UUID đã được cố định để so sánh nội dung. Chi tiết kiểm chứng ở `reports/refactor_verification.json`.

Fixture hồi quy dành cho model, dữ liệu và môi trường đóng gói. Nếu chủ động đổi model hoặc huấn luyện lại, cần đánh giá lại kết quả kỳ vọng; không sửa fixture chỉ để che một lỗi ngoài ý muốn.
