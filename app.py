import streamlit as st
import joblib
import pandas as pd

from src.preprocess import clean_text


@st.cache_resource
def load_model():
    return joblib.load("models/spam_model.pkl")


model = load_model()

tfidf = model.named_steps["tfidf"]
svm = model.named_steps["model"]



st.subheader("Nhập tin nhắn")

message = st.text_area(
    "Message",
    placeholder="Ví dụ: Congratulations! You have won a free prize...",
    height=150,
    label_visibility="collapsed"
)



if st.button("🔍 Predict", use_container_width=True):

    if message.strip() == "":
        st.warning("Vui lòng nhập tin nhắn.")

    else:

        # Tiền xử lý
        cleaned_message = clean_text(message)

        # Dự đoán
        prediction = model.predict([cleaned_message])[0]

        # Decision score
        score = model.decision_function([cleaned_message])[0]


        # =========================
        # Kết quả
        # =========================
        if prediction == "spam":
            st.error("🚨 SPAM")
        else:
            st.success("✅ HAM")


        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Prediction",
                prediction.upper()
            )

        with col2:
            st.metric(
                "Decision Score",
                f"{score:.4f}"
            )


        


       