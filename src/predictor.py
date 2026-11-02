"""Nạp model và dự đoán. Giao diện web và terminal đều dùng chung file này."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import argparse
import json
import joblib

from .preprocessing import validate_text
from .settings import load_config, project_path
from .indicators import analyze_indicators

@dataclass
class Prediction:
    """Giữ nguyên bốn trường kết quả để các phần khác của app sử dụng."""
    label: str
    score: float
    model_id: str
    indicators: list

    def to_dict(self):
        return asdict(self)

class SpamPredictor:
    def __init__(self, model_path=None):
        # Chỉ đọc cấu hình khi người gọi chưa cung cấp đường dẫn model.
        if not model_path:
            model_path = load_config()['model_path']
        self.path = project_path(model_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Không tìm thấy model: {self.path}. Xem README để huấn luyện lại.")
        # Chỉ nạp pickle đi kèm project hoặc model do bạn tự huấn luyện.
        self.model = joblib.load(self.path)
        if list(self.model.classes_) != ['ham', 'spam']:
            raise ValueError("Model phải có hai lớp theo thứ tự ham, spam.")
        model_bytes = self.path.read_bytes()
        model_hash = sha256(model_bytes).hexdigest()[:12]
        self.model_id = self.path.name + ':' + model_hash

    def predict(self, text):
        """Trả về Prediction; giữ nguyên nhãn, điểm SVM và thứ tự dấu hiệu."""
        cleaned = validate_text(text)
        messages = [cleaned]  # scikit-learn nhận một danh sách, kể cả khi chỉ có một tin.
        label = str(self.model.predict(messages)[0])
        score = float(self.model.decision_function(messages)[0])
        findings = analyze_indicators(text)
        return Prediction(label, score, self.model_id, findings)

def main():
    parser = argparse.ArgumentParser(description='Kiểm tra spam bằng cùng model với giao diện web.')
    parser.add_argument('message', nargs='?')
    parser.add_argument('--model')
    args = parser.parse_args()
    try:
        if args.message is not None:
            text = args.message
        else:
            text = input('Nhập tin nhắn: ')
        predictor = SpamPredictor(args.model)
        prediction = predictor.predict(text)
        result = prediction.to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, str(exc) + '\n')

if __name__ == '__main__':
    main()
