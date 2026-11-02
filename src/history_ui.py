"""Giao diện xem lịch sử; phần SQL nằm riêng trong history.py."""
from datetime import datetime
from math import ceil
from zoneinfo import ZoneInfo
import streamlit as st

from .history import list_history, delete_history

LABELS = {'spam': 'Spam', 'ham': 'Không phải spam', 'danger': 'Link được cảnh báo',
          'no_match': 'Link chưa thấy cảnh báo', 'error': 'Link chưa kiểm tra được'}


def render_history():
    """Chỉ hiển thị, lọc và xóa dữ liệu; không tạo lượt kiểm tra mới."""
    with st.expander('🕘 Lịch sử kiểm tra', expanded=False):
        st.caption('Lịch sử chung trên máy · Giờ Việt Nam')
        kind_label = st.selectbox('Loại kiểm tra', ['Tất cả', 'Tin nhắn', 'Đường link'], key='history_kind')
        status_options = ['Tất cả'] + list(LABELS.values())
        status_label = st.selectbox('Kết quả cần xem', status_options, key='history_status')
        search = st.text_input('Tìm trong nội dung lịch sử', key='history_search', max_chars=200)
        if kind_label == 'Tin nhắn':
            kind = 'message'
        elif kind_label == 'Đường link':
            kind = 'link'
        else:
            kind = None

        status = None
        for status_code, display_label in LABELS.items():
            if display_label == status_label:
                status = status_code
                break
        fingerprint = (kind, status, search)
        if st.session_state.get('history_filters') != fingerprint:
            st.session_state.history_filters = fingerprint
            st.session_state.history_page = 1
        try:
            _, total = list_history(kind=kind, status=status, search=search, limit=1)
            pages = max(1, ceil(total / 20))
            # Khi số trang giảm sau khi xóa/lọc, không để người dùng ở trang quá lớn.
            st.session_state.history_page = min(st.session_state.get('history_page', 1), pages)
            page = st.number_input('Trang lịch sử', min_value=1, max_value=pages, step=1, key='history_page')
            offset = (page - 1) * 20
            rows, _ = list_history(kind=kind, status=status, search=search, limit=20, offset=offset)
            st.caption(f'{total} lượt · Trang {page}/{pages}')
            if not rows:
                st.info('Chưa có lịch sử phù hợp.')
            for row in rows:
                saved_time = datetime.fromisoformat(row['created_at'])
                vietnam_time = saved_time.astimezone(ZoneInfo('Asia/Ho_Chi_Minh'))
                stamp = vietnam_time.strftime('%d/%m/%Y %H:%M:%S')
                with st.container(border=True):
                    st.write(stamp + ' · ' + LABELS.get(row['status'], row['status']))
                    st.code(row['content'], language=None)
                    with st.expander('Chi tiết lần kiểm tra'):
                        if row['kind'] == 'message':
                            st.write('Model:', row['model_id'])
                            st.write('Điểm SVM:', round(row['score'], 4))
                            for finding in row['details'].get('indicators', []):
                                st.write(finding['title'])
                        else:
                            st.write('Nguồn:', row['details'].get('source', 'Google Safe Browsing'))
                            if row['details'].get('threats'):
                                st.write('Loại cảnh báo:', ', '.join(row['details']['threats']))
                            if row['details'].get('message'):
                                st.write(row['details']['message'])
                            st.caption('Kết quả tại thời điểm tra cứu; chưa thấy cảnh báo không có nghĩa link an toàn.')
                    if st.button('Xóa lượt này', key='delete_history_' + row['id']):
                        delete_history(row['id'])
                        st.rerun()
            st.divider()
            with st.form('clear_history_form'):
                confirmed = st.checkbox('Tôi muốn xóa toàn bộ lịch sử trên máy này.', key='confirm_clear_history')
                clear = st.form_submit_button('Xóa toàn bộ lịch sử')
            if clear:
                if confirmed:
                    delete_history()
                    st.rerun()
                else:
                    st.warning('Hãy tích xác nhận trước khi xóa toàn bộ lịch sử.')
        except Exception:
            st.error('Không đọc hoặc xóa được lịch sử. Kiểm tra quyền ghi thư mục data/ và file history.sqlite3.')
