"""Phân tích URL trên máy và tra cứu Google theo yêu cầu; không mở website đích."""
from datetime import datetime, timezone
import ipaddress
import json
import re
import socket
from urllib import error, parse, request

MAX_LINKS = 20
SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'goo.gl', 'cutt.ly', 'rebrand.ly'}
URL_PATTERN = re.compile(
    r'https?://[^\s<>"“”]+|www\.[^\s<>"“”]+|'
    r'(?<![\w@./-])(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'
    r'[a-zA-Z]{2,63}(?::\d+)?(?:/[^\s<>"“”]*)?', re.I)


def extract_urls(text):
    """Tìm URL trong văn bản, bỏ dấu câu thừa và giữ thứ tự xuất hiện."""
    urls = []
    for match in URL_PATTERN.finditer(text):
        url = match.group().rstrip('.,;!?:\'’')
        for closing, opening in [(')', '('), (']', '['), ('}', '{')]:
            while url.endswith(closing) and url.count(closing) > url.count(opening):
                url = url[:-1]
        if url not in urls:
            urls.append(url)
    return urls


def analyze_url(raw):
    """Trả về dictionary mô tả URL; eligible cho biết có được gửi đi tra cứu không."""
    warnings = []
    result = {'original': raw, 'url': None, 'host': None, 'warnings': warnings,
              'eligible': False, 'reason': None}
    if not isinstance(raw, str) or not raw.strip() or len(raw) > 2048:
        result['reason'] = 'URL rỗng hoặc vượt giới hạn 2.048 ký tự.'
        return result
    value = raw.strip()
    if re.search(r'[\x00-\x20\x7f\\]', value):
        result['reason'] = 'URL có khoảng trắng, ký tự điều khiển hoặc dấu gạch chéo không hợp lệ.'
        return result
    if not re.match(r'^[a-z][a-z0-9+.-]*://', value, re.I):
        value = 'https://' + value
        warnings.append('URL không ghi giao thức; tạm chuẩn hóa thành HTTPS để tra cứu.')
    try:
        parts = parse.urlsplit(value)
        if parts.scheme.lower() not in ('http', 'https') or not parts.hostname:
            raise ValueError()
        host = parts.hostname.rstrip('.').encode('idna').decode('ascii').lower()
        port = parts.port  # urllib sẽ báo lỗi nếu cổng không phải số hoặc vượt giới hạn.
        if parts.username is not None or parts.password is not None:
            warnings.append('URL chứa thông tin đăng nhập hoặc dấu @, có thể làm nhầm tên miền thật.')
            result['reason'] = 'Không gửi URL chứa thông tin đăng nhập tới dịch vụ tra cứu.'
            result['host'] = host
            return result
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
            valid_labels = True
            for label in host.split('.'):
                if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label):
                    valid_labels = False
                    break
            if len(host) > 253 or not valid_labels:
                raise ValueError()
        result['host'] = host
        if address:
            warnings.append('URL dùng địa chỉ IP thay vì tên miền.')
            if not address.is_global:
                result['reason'] = 'Địa chỉ IP nội bộ/đặc biệt: không gửi đi tra cứu.'
                return result
        elif '.' not in host or host.endswith(('.localhost', '.local', '.internal', '.test', '.invalid', '.example')):
            result['reason'] = 'Tên miền nội bộ hoặc dành cho thử nghiệm: không gửi đi tra cứu.'
            return result
        if address and address.version == 6:
            hostpart = '[' + host + ']'
        else:
            hostpart = host
        netloc = hostpart
        if port is not None:
            netloc += ':' + str(port)
        # Giữ hoa/thường ở đường dẫn và query. Bỏ fragment sau dấu #.
        normalized = parse.urlunsplit((parts.scheme.lower(), netloc, parts.path or '/', parts.query, ''))
        normalized = parse.quote(normalized, safe=":/?&=;%+@!$'()*,-._~[]")
        if parts.scheme.lower() == 'http':
            warnings.append('URL dùng HTTP, kết nối không được bảo vệ bằng HTTPS; đây chưa phải bằng chứng link độc hại.')
        if host in SHORTENERS:
            warnings.append('Link rút gọn che địa chỉ đích; ứng dụng chưa mở rộng đường dẫn này.')
        has_punycode = False
        for label in host.split('.'):
            if label.startswith('xn--'):
                has_punycode = True
                break
        if has_punycode:
            warnings.append('Tên miền quốc tế hóa (Punycode); cần kiểm tra ký tự dễ gây nhầm, không tự kết luận là giả mạo.')
        if host.count('.') >= 4:
            warnings.append('Tên miền có nhiều cấp; hãy kiểm tra kỹ tên miền thực sự.')
        result['url'] = normalized
        result['eligible'] = True
        return result
    except (ValueError, UnicodeError):
        result['reason'] = 'URL hoặc tên miền không hợp lệ.'
        return result


class LinkCheckError(ValueError):
    """Lỗi đã có thông báo phù hợp để hiện cho người dùng."""
    pass


def lookup_url(raw, api_key, *, timeout=10):
    """Tra cứu một URL; trả về danger/no_match hoặc báo LinkCheckError."""
    info = analyze_url(raw)
    if not info['eligible']:
        raise LinkCheckError(info['reason'])
    if not api_key or not api_key.strip():
        raise LinkCheckError('Chưa có API key Google Safe Browsing. Xem LINK_SETUP.md.')
    body = {
        'client': {'clientId': 'spam-message-checker', 'clientVersion': '1.0'},
        'threatInfo': {'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE'],
                       'platformTypes': ['ANY_PLATFORM'], 'threatEntryTypes': ['URL'],
                       'threatEntries': [{'url': info['url']}]},
    }
    # Chỉ gửi yêu cầu tới Google. URL cần kiểm tra nằm trong JSON, không được mở.
    encoded_key = parse.quote(api_key.strip(), safe='')
    endpoint = 'https://safebrowsing.googleapis.com/v4/threatMatches:find?key=' + encoded_key
    request_body = json.dumps(body).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req = request.Request(endpoint, data=request_body, headers=headers, method='POST')
    try:
        # Không đi theo chuyển hướng, tránh gửi yêu cầu/key tới địa chỉ khác.
        class NoRedirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = request.build_opener(NoRedirect)
        with opener.open(req, timeout=timeout) as response:
            payload = response.read(1_048_577)
        if len(payload) > 1_048_576:
            raise LinkCheckError('Phản hồi dịch vụ vượt giới hạn; chưa kiểm tra được link.')
        data = json.loads(payload)
        if not isinstance(data, dict) or set(data) - {'matches'}:
            raise ValueError()
        matches = data.get('matches', [])
        if not isinstance(matches, list):
            raise ValueError()
        threats = []
        for match in matches:
            if not isinstance(match, dict):
                raise ValueError()
            if not isinstance(match.get('threat'), dict):
                raise ValueError()
            if not isinstance(match.get('threatType'), str):
                raise ValueError()
            if not isinstance(match['threat'].get('url'), str):
                raise ValueError()
            # Mỗi yêu cầu chỉ có một URL: có kết quả khớp thì phải hiện cảnh báo.
            threats.append(match['threatType'])
        if matches:
            status = 'danger'
        else:
            status = 'no_match'
        return {
            'status': status,
            'threats': sorted(set(threats)),
            'url': info['url'],
            'source': 'Google Safe Browsing',
            'checked_at': datetime.now(timezone.utc).isoformat(),
        }
    except error.HTTPError as exc:
        error_messages = {
            400: 'Yêu cầu tra cứu không hợp lệ.',
            401: 'API key không hợp lệ.',
            403: 'API key chưa được cấp quyền hoặc Safe Browsing API chưa được bật.',
            429: 'Đã hết hạn mức tra cứu. Hãy thử lại sau.',
        }
        message = error_messages.get(exc.code, 'Dịch vụ tra cứu đang gặp lỗi.')
        raise LinkCheckError(message + ' Chưa có kết luận về link.') from None
    except (error.URLError, TimeoutError, socket.timeout):
        raise LinkCheckError('Không kết nối được dịch vụ hoặc đã hết thời gian chờ. Chưa kiểm tra được link.') from None
    except (ValueError, UnicodeError, KeyError, TypeError):
        raise LinkCheckError('Phản hồi dịch vụ không hợp lệ. Chưa kiểm tra được link.') from None
