"""Tính các chỉ số đánh giá và lưu báo cáo. Không huấn luyện trên tập đánh giá."""
import argparse
import json
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from .preprocessing import clean_text
from .settings import project_path
from .predictor import SpamPredictor

def metrics(y_true, y_pred):
    """Trả về các chỉ số trong dictionary; lớp dương luôn là spam."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, pos_label='spam', average='binary', zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=['ham','spam']).tolist()
    true_negatives, false_positives = matrix[0]
    false_negatives, true_positives = matrix[1]
    number_of_ham_messages = true_negatives + false_positives
    if number_of_ham_messages:
        false_positive_rate = false_positives / number_of_ham_messages
    else:
        false_positive_rate = None
    return {
        'n': len(y_true),
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'spam_precision': float(precision),
        'spam_recall': float(recall),
        'spam_f1': float(f1),
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'false_positive_rate': false_positive_rate,
        'confusion_matrix_ham_spam': matrix,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, help='CSV UTF-8 với cột label,message; dùng dữ liệu độc lập.')
    parser.add_argument('--model')
    parser.add_argument('--output', default='reports/independent_evaluation.json')
    args = parser.parse_args()
    df = pd.read_csv(args.csv, encoding='utf-8-sig', keep_default_na=False)
    if not {'label','message'}.issubset(df.columns) or df.empty:
        parser.error('CSV phải có ít nhất một dòng với cột label,message.')
    raw = df['label'].astype(str).str.strip().str.lower()
    labels = raw.map({'0':'ham','1':'spam','ham':'ham','spam':'spam'})
    messages = df['message'].map(clean_text)
    if labels.isna().any() or (messages.str.len() == 0).any():
        parser.error('CSV có nhãn không hợp lệ hoặc nội dung trống.')
    predictor = SpamPredictor(args.model)
    predictions = predictor.model.predict(messages)
    report = {
        'model_id': predictor.model_id,
        'evaluation_csv': str(args.csv),
        'metrics': metrics(labels, predictions),
    }
    path = project_path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
