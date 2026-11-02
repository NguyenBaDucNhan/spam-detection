"""Đọc, làm sạch và chia dữ liệu. Không sửa các file CSV gốc."""
import re
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from .settings import ROOT, load_config
from .preprocessing import clean_text

SOURCES = {
    'sms_en': ('spam.csv', 'latin-1'),
    'sms_vi': ('full_dataset.csv', 'utf-8-sig'),
    'email_vi_synthetic': ('email_spam_vietnamese.csv', 'utf-8-sig'),
}

def read_source(source):
    """Trả về DataFrame có ba cột label, message, source của một nguồn."""
    if source not in SOURCES:
        raise ValueError(f'Nguồn dữ liệu không hợp lệ: {source}')
    filename, encoding = SOURCES[source]
    df = pd.read_csv(ROOT / 'data' / filename, encoding=encoding)
    if source == 'sms_en':
        df = df.rename(columns={'v1':'label', 'v2':'message'})
    if not {'label', 'message'}.issubset(df.columns):
        raise ValueError(f'{filename} cần có cột label,message')
    df = df[['label', 'message']].dropna().copy()
    raw_labels = df['label'].astype(str).str.strip().str.lower()
    label_mapping = {'0': 'ham', '1': 'spam', 'ham': 'ham', 'spam': 'spam'}
    df['label'] = raw_labels.map(label_mapping)
    if df['label'].isna().any():
        raise ValueError(f'{filename} có nhãn không hợp lệ')
    df['message'] = df['message'].astype(str).map(clean_text)
    df = df[df['message'].str.len() > 0].copy()
    df['source'] = source
    return df

def load_dataset(sources=None):
    """Gộp các nguồn, loại nhãn mâu thuẫn rồi loại tin nhắn trùng hoàn toàn."""
    sources = sources or load_config()['default_sources']
    dataframes = []
    for source in sources:
        source_data = read_source(source)
        dataframes.append(source_data)
    combined = pd.concat(dataframes, ignore_index=True)
    label_counts = combined.groupby('message')['label'].nunique()
    conflicts = set(label_counts[label_counts > 1].index)
    combined = combined[~combined['message'].isin(conflicts)]
    return combined.drop_duplicates('message').reset_index(drop=True)

def template_key(text):
    # Câu chỉ khác URL hoặc token chứa số được gom vào cùng nhóm.
    text = clean_text(text)
    text = re.sub(r'https?://\S+|www\.\S+', '<url>', text)
    text = re.sub(r'\b[^\s]*\d[^\s]*', '<number>', text)
    return text

def split_dataset(df):
    """Lấy fold đầu làm test; giữ nguyên cách chia và seed của bản trước."""
    groups = df['message'].map(template_key)
    strata = df['source'] + ':' + df['label']
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=30)
    train_indices, test_indices = next(splitter.split(df['message'], strata, groups))
    train = df.iloc[train_indices].copy()
    test = df.iloc[test_indices].copy()
    train_groups = set(train['message'].map(template_key))
    test_groups = set(test['message'].map(template_key))
    if train_groups & test_groups:
        raise AssertionError('Rò rỉ nhóm mẫu giữa train/test')
    if set(train['label']) != {'ham', 'spam'} or set(test['label']) != {'ham', 'spam'}:
        raise ValueError('Cần đủ hai lớp trong cả tập train và test.')
    return train, test
