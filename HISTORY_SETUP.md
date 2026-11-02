# Lịch sử kiểm tra trên máy

## Sử dụng

1. Chạy app bằng `run_windows.bat`. Công tắc **Lưu lịch sử kiểm tra trên máy** ngay dưới ô nhập nội dung mặc định bật.
2. Bấm **Kiểm tra tin nhắn** hoặc **Tra cứu link N** như trước.
3. Cuộn xuống cuối trang, mở **Lịch sử kiểm tra**.
4. Lọc theo tin nhắn/đường link, loại kết quả, tìm nội dung (không phân biệt hoa thường, vẫn phân biệt có dấu/không dấu). Mỗi trang hiển thị 20 lượt; đổi số trang để xem thêm.
5. Mở chi tiết để xem model/điểm SVM hoặc nguồn/loại cảnh báo link. Có thể xóa từng lượt hoặc tích xác nhận và bấm xóa toàn bộ lịch sử.

## Lưu những gì?

| Loại lượt kiểm tra | Dữ liệu |
|---|---|
| Tin nhắn | Nội dung cuối cùng sau khi bạn sửa, nhãn spam/ham, điểm SVM, mã model, dấu hiệu quy tắc, thời gian |
| Tra cứu link | URL đã chuẩn hóa được gửi để tra cứu, trạng thái có cảnh báo/chưa thấy cảnh báo/lỗi, nguồn, loại cảnh báo hoặc thông báo lỗi đã làm sạch, thời gian |

- Không lưu ảnh OCR, API key, header HTTP hay toàn bộ phản hồi API.
- Chỉ đọc ảnh OCR hoặc xem phân tích cấu trúc URL không tạo lượt lịch sử. Chỉ bấm phân loại/tra cứu mới tạo bản ghi.
- Mỗi lần bấm kiểm tra tạo một lượt, kể cả cùng nội dung. App tải lại giao diện hoặc gửi phản hồi không tạo thêm lượt kiểm tra.
- Đầu vào rỗng hoặc không hợp lệ không được lưu thành kết quả phân loại.
- Lỗi ghi lịch sử được báo riêng, không làm mất kết quả phân loại/tra cứu.

## Phạm vi người dùng và riêng tư

**Bản này chưa có đăng nhập: lịch sử là kho chung của bản chạy app, không phải lịch sử riêng theo tài khoản.** Mọi người mở cùng bản chạy đều có thể xem và xóa lịch sử chung. Phù hợp để bạn chạy thử cá nhân; trước khi triển khai phục vụ nhiều người với dữ liệu riêng, cần thêm xác thực tài khoản và giới hạn mọi truy vấn theo chủ sở hữu.

- Lưu bằng SQLite tại `data/history.sqlite3`, tồn tại sau khi đóng trình duyệt hoặc khởi động lại app nếu giữ file này.
- Dữ liệu lưu dạng văn bản trong file database, không có mã hóa riêng của ứng dụng. Quyền truy cập phụ thuộc máy và tài khoản hệ điều hành.
- **Tắt công tắc trước khi kiểm tra nội dung riêng tư** để không tạo lượt mới. Tắt công tắc không xóa lượt cũ và không tắt việc gửi URL tới Google khi bạn chủ động tra cứu.
- Trạng thái công tắc giữ trong phiên; phiên mới mặc định bật trở lại.
- Cơ sở dữ liệu lịch sử tách biệt `data/feedback.sqlite3`. Checkbox lưu nội dung khi gửi phản hồi chỉ quản lý bản phản hồi, không quản lý lịch sử. Xóa lịch sử không xóa phản hồi đã gửi, và ngược lại.
- Không dùng lịch sử tự động để huấn luyện model. Nhãn trong lịch sử là dự đoán, không phải nhãn chuẩn.
- Thời gian lưu theo UTC và hiển thị theo múi giờ Việt Nam. Kết quả link cũ có thể đã thay đổi, cần tra cứu lại khi cần.

## Giữ dữ liệu khi nâng cấp

Khi thay project bằng bản ZIP mới, giữ bản sao riêng của `data/history.sqlite3` và `data/feedback.sqlite3` trên máy. Dừng app trước khi sao chép và đưa hai file này vào thư mục `data/` của bản mới nếu muốn giữ dữ liệu cũ. Không đưa các file database chứa nội dung riêng tư lên git hoặc chia sẻ cùng ZIP.

Trong `configs/app.json`, `history_path` cho phép thay vị trí database. Biến môi trường `SPAM_HISTORY_DB` có thể ghi đè vị trí để kiểm thử/triển khai. Không tự đồng bộ lịch sử giữa nhiều máy. Bản ZIP giao cho bạn không có dữ liệu lịch sử hoặc phản hồi mẫu đã lưu.
