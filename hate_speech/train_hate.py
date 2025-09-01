import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import joblib
import os
import pandas as pd              # for data handling
import matplotlib.pyplot as plt  # for plotting
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

csv_path = os.path.join(os.path.dirname(__file__), 'labeled_data.csv')
df = pd.read_csv(csv_path)

df.info()
nltk.download('stopwords')
nltk.download('stopwords')
df["binary_label"] = df["class"].map(lambda x: "Offensive" if x in [0, 1] else "Non-Offensive")
print(df)
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
 # Transformăm clasele în două: Offensive (Hate + Offensive) și Non-Offensive (Neutral)
df["binary_label"] = df["class"].map(lambda x: "Offensive" if x in [0, 1] else "Non-Offensive")

def preprocess_text(text):
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    # Remove user mentions and hashtags
    text = re.sub(r'@\w+|#', '', text)
    # Remove punctuation, numbers, and non-alphabetic characters
    text = re.sub(r'[^a-z\s]', '', text)
    # Tokenize and remove stopwords
    words = text.split()
    words = [word for word in words if word not in stop_words]
    # Stemming
    words = [stemmer.stem(word) for word in words]
    # Join back into string
    return ' '.join(words)


df['clean_tweet'] = df['tweet'].apply(preprocess_text)
print(df.head())


# Visualize the class distribution
plt.pie(df['binary_label'].value_counts().values,
    labels=df['binary_label'].value_counts().index,
    autopct='%1.1f%%')
plt.title("Class Distribution (Binary)")
plt.show()

data = df[["clean_tweet","binary_label"]]
print(data)
print(data['binary_label'].value_counts())


# balancing the data for better accuracy and 
# Extract classes
offensive_df = df[df['binary_label'] == 'Offensive']
non_offensive_df = df[df['binary_label'] == 'Non-Offensive']

# Poți echilibra clasele dacă vrei, de exemplu:
min_count = min(len(offensive_df), len(non_offensive_df))
offensive_df_balanced = offensive_df.sample(n=min_count, random_state=42)
non_offensive_df_balanced = non_offensive_df.sample(n=min_count, random_state=42)
balanced_df = pd.concat([offensive_df_balanced, non_offensive_df_balanced], axis=0).reset_index(drop=True)
plt.pie(balanced_df['binary_label'].value_counts().values,
    labels=balanced_df['binary_label'].value_counts().index,
    autopct='%1.1f%%')
plt.title("Class Distribution (Binary)")
plt.show()


# Step 1: Define X and y
X = balanced_df['clean_tweet']
y = balanced_df['binary_label']

# Step 2: Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 3: Vectorization
vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(X_train)
X_test = vectorizer.transform(X_test)

# Step 4: Random Forest Model
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Step 5: Prediction and Evaluation
y_pred = rf.predict(X_test)
print("Random Forest Classification Report:\n")
print(classification_report(y_test, y_pred))

rf_path = os.path.join(os.path.dirname(__file__), 'rf_hate_speech.pkl')
vectorizer_path = os.path.join(os.path.dirname(__file__), 'vectorizer.pkl')
joblib.dump(rf, rf_path)
joblib.dump(vectorizer, vectorizer_path)