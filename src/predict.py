import joblib

from preprocess import clean_text


model = joblib.load("models/spam_model.pkl")

message = input("Nhập tin nhắn: ")

message = clean_text(message)

prediction = model.predict([message])

print("Kết quả:", prediction[0])