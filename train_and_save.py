import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import string
import nltk
from nltk.stem import PorterStemmer

# --- 1. Data Transformation Function (Copied from app.py) ---
ps = PorterStemmer()

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    # Note: stopwords removal is usually done here, but TfidfVectorizer handles it.
    # We will keep the original logic for compatibility with your app.py's flow.
    for i in text:
        if i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)

# --- 2. Load and Prepare Data ---
try:
    # Change the filename back to 'spam.csv' if that is your file name
    # and add the encoding='latin-1' argument.
    df = pd.read_csv('spam.csv', encoding='latin-1') 
    print("Dataset loaded successfully.")
except FileNotFoundError:
    print("ERROR: spam.csv not found. Please ensure it's in the same directory.")
    exit()

# Apply the text transformation
df['transformed_message'] = df['v2'].apply(transform_text)

# Map labels to numbers (ham=0, spam=1)
df['Category'] = df['v1'].map({'ham': 0, 'spam': 1})

X = df['transformed_message']
y = df['Category']

# Split data into training and testing sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Data split: Training samples={len(X_train)}, Testing samples={len(X_test)}")


# --- 3. Fit Vectorizer and Train Model ---

# Initialize the vectorizer
tfidf_new = TfidfVectorizer()

# ***** THE CRUCIAL STEP THAT WAS MISSING BEFORE *****
# Call .fit_transform() on the training data
X_train_transformed = tfidf_new.fit_transform(X_train)
print("TfidfVectorizer has been fitted and transformed the training data.")

# Initialize and train the model
model_new = MultinomialNB()
model_new.fit(X_train_transformed, y_train)
print("MultinomialNB model has been trained.")


# --- 4. Save the Fitted Vectorizer and Trained Model ---

# Save the FITTED vectorizer
with open('vectorizer.pkl', 'wb') as file:
    pickle.dump(tfidf_new, file)
    
# Save the new model
with open('model.pkl', 'wb') as file:
    pickle.dump(model_new, file)

print("\nSUCCESS: 'vectorizer.pkl' and 'model.pkl' have been saved and are ready for use by app.py.")