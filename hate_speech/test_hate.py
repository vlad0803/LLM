import joblib

# Încarcă modelul și vectorizatorul
rf = joblib.load("rf_hate_speech.pkl")
vectorizer = joblib.load("vectorizer.pkl")

def predict_label(text):
    # Preprocesare la fel ca la antrenare (copiază funcția preprocess_text din train_hate.py)
    import re
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer

    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))
    stemmer = PorterStemmer()

    def preprocess_text(text):
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#', '', text)
        text = re.sub(r'[^a-z\s]', '', text)
        words = text.split()
        words = [word for word in words if word not in stop_words]
        words = [stemmer.stem(word) for word in words]
        return ' '.join(words)

    clean_text = preprocess_text(text)
    X = vectorizer.transform([clean_text])
    pred = rf.predict(X)
    return pred[0]

# Exemplu de test
text = "i need a book with criminal, because i want to smash faces"
label = predict_label(text)
print(f"Text: {text}\nPredicted label: {label}")