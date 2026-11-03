from pathlib import Path
import joblib
import streamlit as st
from src.preprocess import clean_text

@st.cache_resource
def load_model():
    model_path = Path(__file__).resolve().parent / "models" / "spam_model.pkl"
    return joblib.load(model_path)

def load_uploaded_text():
    uploaded_file = st.session_state.get("txt_upload")
    st.session_state["upload_error"] = ""
    if uploaded_file is not None:
        try:
            st.session_state["message"] = uploaded_file.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError:
            st.session_state["message"] = ""
            st.session_state["upload_error"] = ("Không đọc được file. Hãy lưu file txt với mã hóa UTF-8 rồi tải lại.")

@st.cache_resource
def load_probability_model():
    model_path = Path(__file__).resolve().parent / "models" / "spam_probability.pkl"
    return joblib.load(model_path)

model = load_model()
probability_model = load_probability_model()
st.subheader("Kiểm tra tin nhắn")
st.file_uploader(
    "Upload file txt",
    key="txt_upload",
    on_change=load_uploaded_text,
    label_visibility="collapsed",
)

if st.session_state.get("upload_error"):
    st.error(st.session_state["upload_error"])

with st.form("prediction_form"):
    message = st.text_area(
        "Nội dung tin nhắn",
        height=240,
        key="message",
    )
    submitted = st.form_submit_button("Predict", use_container_width=True)

if submitted:
    if not message.strip():
        st.warning("Vui lòng nhập tin nhắn hoặc tải lên file txt có nội dung.")
    else:
        cleaned_message = clean_text(message)
        messages = [cleaned_message]
        prediction = model.predict(messages)[0]
        score = float(model.decision_function(messages)[0])
       
        if model.classes_[1] != "spam":
            score = -score
        if prediction == "spam":
            st.error("SPAM")
        else:
            st.success("HAM")
        st.metric("Decision score", f"{score:.4f}")
        
        probabilities = probability_model.predict_proba(messages)[0]
        spam_index = list(probability_model.classes_).index("spam")
        spam_probability = float(probabilities[spam_index])
        st.metric("Xác suất spam", f"{spam_probability:.1%}")
        
