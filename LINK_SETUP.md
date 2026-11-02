# Kiểm tra link đáng ngờ và tra cứu Google Safe Browsing

## Hai phần độc lập

**Phân tích cấu trúc** dùng Python, không cần key, không gọi mạng: trích xuất URL HTTP/HTTPS, `www.` và một số tên miền dạng thường trong nội dung. Hiển thị tên máy chủ thực tế, HTTP, địa chỉ IP, link rút gọn, tên miền Punycode, nhiều cấp tên miền và URL chứa thông tin đăng nhập. Đây là dấu hiệu để xem xét, không phải model phát hiện mã độc hoặc kết luận website giả mạo.

**Tra cứu trực tuyến** dùng Google Safe Browsing Lookup API v4, cần Internet và API key. Chỉ chạy khi bấm **Tra cứu link N**. Ứng dụng gửi URL chuẩn hóa tới endpoint Google cố định, không gửi toàn bộ tin nhắn, ảnh, số người gửi hoặc kết quả model spam. Không truy cập website đích, chạy JavaScript hay mở rộng link rút gọn.

## Cách dùng ngay

1. Chạy app như trước, nhập tin nhắn hoặc lấy văn bản qua OCR.
2. Xem mục **Kiểm tra đường link**, các dấu hiệu cấu trúc tự hiện trên máy.
3. Muốn tra cứu trực tuyến, mở **Thiết lập tra cứu Google Safe Browsing** và nhập key.
4. Xem chính xác URL sẽ gửi; chỉ bấm **Tra cứu link** nếu đồng ý gửi URL này tới Google. URL có thể chứa mã đăng nhập hoặc dữ liệu riêng tư trong đường dẫn/tham số; đừng gửi các link đó.
5. Kết quả link hiển thị riêng, không tự đổi nhãn spam và không ghi vào database phản hồi.

Không có key vẫn dùng được phân tích cấu trúc, phân loại spam, OCR và phản hồi.

## Tạo API key

Safe Browsing API dành cho **mục đích phi thương mại**; nếu dùng để bán sản phẩm hoặc tạo doanh thu, xem Google Cloud Web Risk thay thế. Bản này chỉ tích hợp Safe Browsing, chưa tích hợp Web Risk.

1. Vào https://console.cloud.google.com/ và tạo/chọn một Google Cloud project của bạn.
2. Trong **APIs & Services → Library**, tìm và bật **Safe Browsing API**.
3. Trong **APIs & Services → Credentials**, chọn **Create credentials → API key**.
4. Trong cài đặt key, giới hạn API được sử dụng là Safe Browsing API. Đây là yêu cầu từ backend Python; giới hạn kiểu HTTP referrer của website không phù hợp với luồng này. Có thể dùng giới hạn IP nếu có IP đầu ra ổn định.
5. Dán key vào ô mật khẩu trong app. Không chia sẻ key, không gửi key trong chat, không đưa key vào git/ZIP.

Hoặc thiết lập key bằng biến môi trường trước khi chạy app:

**PowerShell:**

```powershell
$env:SAFE_BROWSING_API_KEY = 'KEY_CUA_BAN'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**CMD:**

```cmd
set "SAFE_BROWSING_API_KEY=KEY_CUA_BAN"
.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux:**

```bash
export SAFE_BROWSING_API_KEY='KEY_CUA_BAN'
.venv/bin/python -m streamlit run app.py
```

Key trong ô nhập chỉ giữ trong phiên; biến môi trường chỉ áp dụng cho tiến trình/terminal đang dùng. Code không lưu key hay toàn bộ phản hồi API và không hiển thị nội dung lỗi HTTP thô có thể lộ key. Khi bật lưu lịch sử, URL, kết quả rút gọn và thời gian được lưu trong history.sqlite3 (xem HISTORY_SETUP.md). Không có key mẫu thực trong project.

## Đọc kết quả

| Kết quả | Ý nghĩa |
|---|---|
| Google cảnh báo link có thể nguy hiểm | URL có khớp danh sách MALWARE, SOCIAL_ENGINEERING hoặc UNWANTED_SOFTWARE trong lần tra cứu |
| Chưa tìm thấy cảnh báo | Google không trả kết quả khớp; **không có nghĩa URL an toàn** |
| Dấu hiệu cấu trúc | Quy tắc Python tìm thấy điểm cần xem xét, có thể báo nhầm |
| Chưa tra cứu / chưa kiểm tra được | Không có kết luận từ Google; chưa bấm nút, thiếu key, hết quota, lỗi mạng hoặc phản hồi lỗi |

Mỗi kết quả trực tuyến có thời điểm UTC. Kết quả giữ trong phiên để xem và được ghi lịch sử nếu bật công tắc; không tự cập nhật theo thời gian. Sửa nội dung tin nhắn chỉ xóa kết quả đang hiển thị trong phiên, không xóa lịch sử đã ghi. Bấm tra cứu lại để lấy kết quả mới. Một link chưa được cảnh báo vẫn có thể là nguy hiểm, nhất là link mới.

## Giới hạn kỹ thuật

- Tối đa 20 link đầu mỗi nội dung, tối đa 2.048 ký tự mỗi URL, khoảng 10 giây chờ cho một yêu cầu.
- Bỏ phần fragment `#...` khi tra cứu, giữ nguyên hoa/thường của đường dẫn/tham số. Nếu URL chưa có giao thức thì tạm thêm HTTPS, hiển thị URL chuẩn hóa trước khi gửi.
- Từ chối URL sai định dạng, chứa tài khoản/mật khẩu, IP nội bộ/đặc biệt, tên miền nội bộ hoặc đuôi thử nghiệm. Không phân giải DNS hoặc gửi yêu cầu đến URL người dùng đưa vào.
- Trích xuất URL theo quy tắc có thể bỏ sót tên miền Unicode không ghi giao thức, URL viết né lọc như `hxxps` / `[.]`, hoặc lấy nhầm chuỗi trông giống tên miền. URL Unicode có `https://` được chuẩn hóa IDNA.
- Không đánh giá nội dung website, file tải xuống, chuỗi chuyển hướng hay sự tương đồng thương hiệu. HTTP, link rút gọn và Punycode không tự đồng nghĩa với độc hại; HTTPS không đảm bảo an toàn.
- Đã kiểm tra tích hợp HTTP bằng phản hồi mô phỏng. **Chưa kiểm tra gọi Google thật do chưa có key của người dùng.** Không coi bộ test mô phỏng là benchmark phát hiện lừa đảo.

## Tham khảo chính thức

- Lookup API: https://developers.google.com/safe-browsing/v4/lookup-api
- API key: https://developers.google.com/safe-browsing/v4/get-started
- Phạm vi phi thương mại: https://developers.google.com/safe-browsing
- Dịch vụ thương mại: https://cloud.google.com/web-risk
