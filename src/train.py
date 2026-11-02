"""Huấn luyện theo từng bước: đọc dữ liệu → chia tập → học → đánh giá → lưu."""
import argparse
import json
import platform
from datetime import datetime, timezone
import joblib
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from .dataset import load_dataset, split_dataset, SOURCES
from .evaluate import metrics
from .settings import project_path

def main():
    # 1. Đọc lựa chọn từ terminal. Mở app sẽ không tự gọi hàm này.
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', nargs='+', choices=list(SOURCES))
    parser.add_argument('--analyzer', choices=['char','word'], default='char')
    parser.add_argument('--output', default='models/spam_retrained.pkl',
                        help='Mặc định lưu model mới, giữ nguyên model đóng gói.')
    args = parser.parse_args()

    # 2. Làm sạch dữ liệu và chia train/test trước khi học TF-IDF.
    df = load_dataset(args.sources)
    train, test = split_dataset(df)

    # 3. Giữ nguyên đặc trưng và tham số model để không đổi cách huấn luyện.
    if args.analyzer == 'char':
        ngram_range = (3, 5)
    else:
        ngram_range = (1, 2)
    model = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer=args.analyzer,
            ngram_range=ngram_range,
            min_df=2,
            max_features=120000,
            sublinear_tf=True,
        )),
        ('model', LinearSVC(C=1.0, class_weight='balanced', random_state=30)),
    ])
    model.fit(train['message'], train['label'])
    predicted = model.predict(test['message'])

    # 4. Lưu model mới, không tự thay model đang dùng trong cấu hình app.
    output = project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    root = project_path('.')
    if output.is_relative_to(root):
        report_model_path = str(output.relative_to(root))
    else:
        report_model_path = str(output)

    # Tính riêng từng nguồn để không đánh đồng SMS với email tổng hợp.
    source_reports = {}
    for source, source_data in test.groupby('source'):
        source_predictions = model.predict(source_data['message'])
        source_reports[source] = metrics(source_data['label'], source_predictions)
    report = {
        'trained_at':datetime.now(timezone.utc).isoformat(),
        'model_path': report_model_path,
        'versions':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'sources_after_cleaning':df['source'].value_counts().to_dict(),
        'train_samples':len(train), 'test_samples':len(test),
        'split':'StratifiedGroupKFold 5 folds; first fold as holdout; seed=30; groups normalize URLs/numeric tokens',
        'note':'Grouping is heuristic, not semantic deduplication. Synthetic results do not validate real-world performance.',
        'overall_test':metrics(test['label'], predicted),
        'by_source_test': source_reports,
    }
    output.with_suffix('.metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # 5. Lưu các dự đoán test và các lỗi để kiểm tra thủ công.
    report_dir = project_path('reports') / output.stem
    report_dir.mkdir(parents=True, exist_ok=True)
    audit = test.copy()
    audit['predicted'] = predicted
    audit.to_csv(report_dir/'test_predictions.csv',index=False,encoding='utf-8-sig')
    errors = audit[audit['label'] != audit['predicted']]
    errors.to_csv(report_dir/'errors.csv', index=False, encoding='utf-8-sig')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('Model saved:', output)
    print('Để dùng model mới, sửa model_path trong configs/app.json và khởi động lại ứng dụng.')

if __name__ == '__main__':
    main()
