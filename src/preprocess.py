import pandas as pd
import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def load_data():
    df = pd.read_csv("data/spam.csv", encoding = "latin-1")
    df = df[["v1","v2"]]
    df.columns = ["label","message"]
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)
    df["message"] = df["message"].apply(clean_text)
    return df


