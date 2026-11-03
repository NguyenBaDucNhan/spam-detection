from sklearn.metrics import(
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
def evaluate_model(y_test,y_pred):
    accurracy = accuracy_score(y_test,y_pred)
    precision = precision_score(y_test,y_pred,pos_label="spam")
    recall = recall_score(y_test,y_pred,pos_label="spam")
    f1 = f1_score(y_test,y_pred,pos_label="spam")
    print("Accuracy:", accurracy)
    print("Precision:", precision)
    print("Recall:",recall)
    print("F1:",f1)
    print("Confusion Matrix:")
    print(confusion_matrix(y_test,y_pred))
    print("Classification report")
    print(classification_report(y_test,y_pred))
    
