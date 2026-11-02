"""Chạy: python -m streamlit run app.py. Đọc theo các phần đánh số bên dưới."""
import streamlit as st
import os
from src.predictor import SpamPredictor
from src.feedback import save_feedback
from src.preprocessing import MAX_TEXT_LENGTH
from src.settings import load_config, project_path
from src.ocr import extract_text, OCRError
from src.link_check import extract_urls, analyze_url, lookup_url, LinkCheckError, MAX_LINKS
from src.history import save_message, save_link
from src.history_ui import render_history

# 1. Cấu hình trang và nạp model một lần bằng cache của Streamlit.
st.set_page_config(page_title='Kiểm tra tin nhắn', page_icon='🛡️', layout='centered')

@st.cache_resource
def load_predictor(path, modified_at):
    # modified_at nằm trong khóa cache: file model thay đổi thì nạp lại.
    return SpamPredictor(path)

config = load_config()
model_path = project_path(config['model_path'])
try:
    predictor = load_predictor(str(model_path), model_path.stat().st_mtime_ns)
except Exception:
    st.error('Không thể nạp model. Kiểm tra file trong models/ và cài đúng requirements.txt; xem README.md.')
    st.stop()

# 2. Tiêu đề. Công tắc lưu lịch sử nằm cạnh phần nhập nội dung ở dưới.
st.title('🛡️ Kiểm tra tin nhắn')

# 3. OCR: chỉ điền văn bản, người dùng sửa rồi chủ động bấm phân loại.
with st.expander('📷 Đọc tin nhắn từ ảnh', expanded=False):
    uploaded = st.file_uploader(
        'Chọn ảnh tin nhắn', type=['png', 'jpg', 'jpeg', 'webp'], key='ocr_image',
        help='PNG, JPG hoặc WebP; tối đa 8 MB và 16 triệu điểm ảnh. Nên cắt sát vùng tin nhắn.',
    )
    language_name = st.selectbox('Ngôn ngữ trong ảnh', ['Tiếng Việt + tiếng Anh', 'Tiếng Việt', 'Tiếng Anh'])
    language_codes = {
        'Tiếng Việt + tiếng Anh': 'vie+eng',
        'Tiếng Việt': 'vie',
        'Tiếng Anh': 'eng',
    }
    language = language_codes[language_name]
    if uploaded is not None:
        image_bytes = uploaded.getvalue()
        # Kiểm tra ảnh trước khi đưa vào phần hiển thị.
        try:
            from src.ocr import prepare_image
            preview = prepare_image(image_bytes)
            st.image(preview, width=450)
        except OCRError as exc:
            st.warning(str(exc))
        else:
            if st.button('Trích xuất chữ từ ảnh', use_container_width=True):
                try:
                    with st.spinner('Đang đọc chữ trong ảnh…'):
                        ocr_result = extract_text(image_bytes, language)
                    if len(ocr_result.text) > MAX_TEXT_LENGTH:
                        st.warning('Văn bản đọc được vượt giới hạn 20.000 ký tự. Hãy cắt ảnh chỉ còn vùng tin nhắn rồi thử lại.')
                    else:
                        # Gán trước khi tạo ô nhập ở phần 4; không tự phân loại.
                        st.session_state.message_input = ocr_result.text
                        st.session_state.pop('result', None)
                        st.success('Đã đọc chữ. Kiểm tra và sửa nội dung bên dưới trước khi phân loại.')
                except OCRError as exc:
                    st.warning(str(exc))

# 4. Ô nhập chung cho nội dung gõ tay và văn bản OCR.
message = st.text_area('Nội dung tin nhắn', key='message_input', height=170,
    max_chars=MAX_TEXT_LENGTH, placeholder='Dán tin nhắn bạn muốn kiểm tra vào đây…')
save_history = st.checkbox(
    'Lưu lịch sử kiểm tra trên máy', value=True, key='save_history',
    help='Lưu nội dung và kết quả trên máy chạy app. Lịch sử dùng chung vì chưa có đăng nhập; không lưu ảnh hoặc API key.',
)

# 5. Phân tích cấu trúc URL; chỉ gọi Google khi người dùng bấm tra cứu.
st.subheader('🔗 Kiểm tra đường link')
with st.expander('Thiết lập tra cứu Google Safe Browsing'):
    provided_key = st.text_input(
        'API key Safe Browsing (tùy chọn)', type='password', key='safe_browsing_key',
        placeholder='Nhập API key của Google',
        help='Chỉ cần cho tra cứu trực tuyến. URL cần kiểm tra được dán vào ô Nội dung tin nhắn, không phải ô này.',
    )
api_key = provided_key.strip()
if not api_key:
    api_key = os.environ.get('SAFE_BROWSING_API_KEY', '').strip()
urls = extract_urls(message)
if st.session_state.get('link_source') != message:
    st.session_state.link_source = message
    st.session_state.link_results = {}
if not urls:
    st.caption('Dán URL vào ô nội dung để kiểm tra link.')
else:
    st.caption('Bấm tra cứu sẽ gửi URL tới Google. Tránh dùng link chứa thông tin riêng tư.')
    if len(urls) > MAX_LINKS:
        st.warning(f'Tìm thấy {len(urls)} link; chỉ hiển thị {MAX_LINKS} link đầu. Hãy kiểm tra phần còn lại riêng.')
    for index, url in enumerate(urls[:MAX_LINKS], 1):
        info = analyze_url(url)
        with st.container(border=True):
            st.write(f'Link {index}')
            st.code(url, language=None)
            if info['host']:
                st.write('Tên miền:', info['host'])
            for warning in info['warnings']:
                st.warning(warning)
            if not info['warnings']:
                st.caption('Chưa thấy dấu hiệu bất thường trong cấu trúc URL.')
            if not info['eligible']:
                st.info(info['reason'])
            else:
                if info['url'] != url:
                    st.caption('URL sẽ gửi để tra cứu:')
                    st.code(info['url'], language=None)
                if st.button(f'Tra cứu link {index}', key=f'lookup_{index}', disabled=not bool(api_key)):
                    try:
                        with st.spinner('Đang tra cứu Google Safe Browsing…'):
                            st.session_state.link_results[url] = lookup_url(url, api_key)
                    except LinkCheckError as exc:
                        st.session_state.link_results[url] = {'status':'error', 'message':str(exc)}
                    if save_history:
                        try:
                            save_link(info['url'], st.session_state.link_results[url])
                        except Exception:
                            st.warning('Đã tra cứu nhưng chưa lưu được lịch sử. Kiểm tra quyền ghi thư mục data/.')
                remote = st.session_state.link_results.get(url)
                if remote:
                    if remote['status'] == 'danger':
                        st.error('Google Safe Browsing cảnh báo: link này có thể nguy hiểm.')
                        st.write('Loại cảnh báo:', ', '.join(remote['threats']))
                    elif remote['status'] == 'no_match':
                        st.info('Google Safe Browsing: chưa tìm thấy cảnh báo. Không có nghĩa link an toàn.')
                    else:
                        st.warning('Chưa kiểm tra được: ' + remote['message'])
                    if remote.get('checked_at'):
                        st.caption('Tra cứu lúc (UTC): ' + remote['checked_at'])
                else:
                    if not api_key:
                        st.caption('Nhập API key để tra cứu trực tuyến.')

# 6. Dự đoán và lưu đúng một lượt lịch sử cho mỗi lần bấm kiểm tra.
if st.button('Kiểm tra tin nhắn', type='primary', use_container_width=True):
    try:
        prediction = predictor.predict(message)
        st.session_state.result = {'text':message, 'prediction':prediction}
        st.session_state.feedback_saved = False
        st.session_state.pop('feedback_label', None)
        st.session_state.pop('consent_text', None)
        if save_history:
            try:
                save_message(message, prediction)
            except Exception:
                st.warning('Đã phân loại nhưng chưa lưu được lịch sử. Kiểm tra quyền ghi thư mục data/.')
    except ValueError as exc:
        st.session_state.pop('result', None)
        st.warning(str(exc))

# Streamlit chạy lại file sau mỗi tương tác. Chỉ hiện kết quả nếu nội dung/model còn khớp.
stored = st.session_state.get('result')
if stored and (stored['text'] != message or stored['prediction'].model_id != predictor.model_id):
    st.info('Nội dung hoặc model đã thay đổi. Bấm kiểm tra để xem kết quả mới.')
    stored = None

# 7. Hiện kết quả và nhận phản hồi; gửi phản hồi không tự tạo thêm lượt lịch sử.
if stored:
    result = stored['prediction']
    if result.label == 'spam':
        st.error('Model đánh giá: Có khả năng là spam')
    else:
        st.success('Model đánh giá: Không phải spam')

    st.subheader('Dấu hiệu cần xem xét', help='Các dấu hiệu được tìm bằng quy tắc, độc lập với model phân loại spam.')
    if not result.indicators:
        st.write('Chưa tìm thấy dấu hiệu đáng ngờ theo quy tắc.')
    for item in result.indicators:
        with st.container(border=True):
            st.write(item['title'])
            st.code(item['evidence'], language=None)
            st.write(item['advice'])

    with st.expander('Thông tin kỹ thuật'):
        st.write('Nhãn:', result.label)
        st.write('Điểm quyết định SVM:', round(result.score, 4))
        st.caption('Điểm SVM không phải xác suất. Nhãn không spam không đảm bảo nội dung an toàn.')
        st.code(result.model_id, language=None)

    st.divider()
    st.subheader('Bạn đánh giá tin nhắn này thế nào?')
    if st.session_state.get('feedback_saved'):
        st.success('Đã lưu phản hồi trên máy chạy ứng dụng. Cảm ơn bạn!')
    else:
        if result.label == 'ham':
            feedback_default = 0
        else:
            feedback_default = 1
        with st.form('feedback_form'):
            actual = st.radio('Nhãn bạn cho là đúng', ['Không phải spam', 'Spam'],
                              key='feedback_label', index=feedback_default,
                              horizontal=True)
            consent = st.checkbox(
                'Tôi đồng ý lưu cả nội dung tin nhắn để cải thiện model.',
                key='consent_text', value=False,
                help='Áp dụng cho phản hồi. Lưu lịch sử được bật/tắt riêng ở dưới ô nhập nội dung.',
            )
            submitted = st.form_submit_button('Gửi phản hồi')
        if submitted:
            try:
                if actual == 'Spam':
                    actual_label = 'spam'
                else:
                    actual_label = 'ham'
                save_feedback(stored['text'], result, actual_label, save_text=consent)
                st.session_state.feedback_saved = True
                st.rerun()
            except OSError:
                st.error('Chưa lưu được phản hồi. Kiểm tra quyền ghi thư mục data/.')
            except Exception:
                st.error('Chưa lưu được phản hồi. Kiểm tra cơ sở dữ liệu phản hồi và thử lại.')

# 8. Lịch sử: đọc dữ liệu đã lưu, không chạy lại model hoặc tra cứu link.
st.divider()
render_history()
