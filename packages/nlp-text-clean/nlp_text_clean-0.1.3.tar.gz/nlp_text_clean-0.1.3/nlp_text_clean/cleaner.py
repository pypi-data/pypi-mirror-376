# textcleaner/cleaner.py

import re
import string
import spacy
from nltk.corpus import stopwords as nltk_stopwords
from nltk.stem import PorterStemmer
import nltk

# Download stopwords if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class TextCleaner:
    def __init__(self,
                 remove_numbers=True,
                 remove_punctuation=True,
                 remove_special_chars=True,
                 use_stemming=False,
                 use_lemmatization=True,
                 language="english",
                 custom_stopwords=None,
                 preserve_num_token=False,
                 remove_html_tags=False,
                 remove_urls=False):
        """
        Parameters
        ----------
        remove_numbers : bool
            Remove numbers from text.
        remove_punctuation : bool
            Remove punctuation marks.
        remove_special_chars : bool
            Remove special characters.
        use_stemming : bool
            Apply stemming instead of lemmatization.
        use_lemmatization : bool
            Apply lemmatization (default True).
        language : str
            Language for stopwords (default "english").
        custom_stopwords : list
            Custom stopword list (extends or replaces default).
        preserve_num_token : bool
            Replace numbers with <NUM> instead of removing them.
        """

        self.remove_numbers = remove_numbers
        self.remove_punctuation = remove_punctuation
        self.remove_special_chars = remove_special_chars
        self.use_stemming = use_stemming
        self.use_lemmatization = use_lemmatization
        self.language = language
        self.preserve_num_token = preserve_num_token
        self.remove_html_tags = remove_html_tags
        self.remove_urls = remove_urls

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        except OSError:
            raise Exception("SpaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")

        # Stopwords
        self.stopwords = set(nltk_stopwords.words(language))
        if custom_stopwords:
            self.stopwords = self.stopwords.union(set(custom_stopwords))

        # Stemming
        self.stemmer = PorterStemmer()

    def clean_text(self, text: str) -> str:
        """
        Clean input text based on configuration.
        """
        if not isinstance(text, str):
            return ""

        # 1. Lowercase
        text = text.lower()

        # 2. Remove special characters
        if self.remove_special_chars:
            text = re.sub(r"[^a-zA-Z0-9\s.,!?]", " ", text)

        # 3. Remove punctuation
        if self.remove_punctuation:
            text = text.translate(str.maketrans("", "", string.punctuation))

        # 4. Handle numbers
        if self.remove_numbers:
            if self.preserve_num_token:
                text = re.sub(r"\d+", "NUMTOKEN", text)
            else:
                text = re.sub(r"\d+", " ", text)
        #5. Remove HTML tags
        if self.remove_html_tags:
            text = re.sub(r"<.*?>", " ", text)

        # 6. Remove URLs
        if self.remove_urls:
            text = re.sub(r"http\S+|www\S+|https\S+", " ", text, flags=re.MULTILINE)

        # 7. Remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()


        # 8. Tokenize with spaCy
        doc = self.nlp(text)

        cleaned_tokens = []
        for token in doc:
            if token.text in self.stopwords:
                continue

            if self.use_stemming:
                cleaned_tokens.append(self.stemmer.stem(token.text))
            elif self.use_lemmatization:
                cleaned_tokens.append(token.lemma_)
            else:
                cleaned_tokens.append(token.text)
        # Replace NUMTOKEN back to <NUM>
        if self.preserve_num_token:
            cleaned_tokens = ["<NUM>" if t == "NUMTOKEN" or t=="numtoken" else t for t in cleaned_tokens]
        
        return " ".join(cleaned_tokens)
