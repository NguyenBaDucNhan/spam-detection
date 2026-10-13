from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.metrics import make_scorer, f1_score
from preprocess import load_data
from evaluate import evaluate_model
import joblib
from sklearn.model_selection import GridSearchCV

df = load_data()
X = df["message"]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(X,y,train_size = 0.8,random_state = 30, stratify = y)



models = {
    "Naive Bayes": MultinomialNB(),
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Linear SVM": LinearSVC()
}

spam_f1 = make_scorer(
    f1_score,
    pos_label="spam"
)

for name, model in models.items():

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("model", model)
    ])

    scores = cross_val_score(
        pipeline,
        X_train,
        y_train,
        cv=5,
        scoring=spam_f1
    )

    print("\n", name)
    print("F1 từng fold:", scores)
    print("F1 trung bình:", scores.mean())



pipeline = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("model", LinearSVC())
])


param_grid = {
    "tfidf__ngram_range": [
        (1, 1),
        (1, 2)
    ],

    "tfidf__min_df": [
        1,
        2
    ],

    "model__C": [
        0.1,
        1,
        10
    ],

    "model__class_weight": [
        None,
        "balanced"
    ]
}


grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring=spam_f1,
    n_jobs=-1
)


grid_search.fit(X_train, y_train)


print("\nBest parameters:")
print(grid_search.best_params_)

print("\nBest CV F1:")
print(grid_search.best_score_)


best_model = grid_search.best_estimator_


y_pred = best_model.predict(X_test)

print("\nFINAL TEST:")
evaluate_model(y_test, y_pred)


joblib.dump(
    best_model,
    "models/spam_model.pkl"
)
import pandas as pd

result = pd.DataFrame({
    "message": X_test,
    "actual": y_test,
    "predicted": y_pred
})

false_negative = result[
    (result["actual"] == "spam") &
    (result["predicted"] == "ham")
]

for message in false_negative["message"]:

    score = best_model.decision_function([message])[0]

    print("Message:", message)
    print("Score:", score)
    print("--------------------")