# NLP Text Cleaner

[![PyPI Version](https://img.shields.io/pypi/v/nlp-text-clean)](https://pypi.org/project/nlp-text-clean/)
[![License](https://img.shields.io/pypi/l/nlp-text-clean)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/nlp-text-clean)](https://pypi.org/project/nlp-text-clean/)

A lightweight, configurable Python library for **text preprocessing** in NLP tasks.  
It helps you clean raw text by lowercasing, removing noise, lemmatizing, and more — ready for **machine learning** or **deep learning** models.

---

## ✨ Features
- Convert text to lowercase  
- Remove special characters  
- Remove punctuation (optional)  
- Remove numbers or replace them with `<NUM>` token  
- Remove extra spaces  
- Lemmatization (default) or stemming (optional)  
- Stopword removal (customizable)  
- Multi-language support (via **NLTK** / **spaCy**)  
- Add your own **custom stopwords**  



## Installation

From **PyPI**:
```bash
pip install nlp-text-clean
From TestPyPI (for testing):

🚀 Usage
python

from nlp_text_clean.cleaner import TextCleaner

# Initialize with custom options
cleaner = TextCleaner(
    remove_numbers=True,
    remove_punctuation=True,
    remove_special_chars=True,
    use_stemming=False,
    use_lemmatization=True,
    language="english",
    custom_stopwords=None,
    preserve_num_token=False,
    remove_html_tags=False,
    remove_urls=False
)

text = "He scored 100 marks!!! Running better than others."
cleaned = cleaner.clean_text(text)

print(cleaned)
# Output: "score <NUM> mark run well"
```

## Parameters
| Parameter Name        | Type         | Default   | Description                                      |
|-----------------------|--------------|-----------|--------------------------------------------------|
| remove_numbers        | bool         | False     | Remove numbers from text                         |
| preserve_num_token    | bool         | False     | Replace numbers with `<NUM>` token               |
| remove_punctuation    | bool         | True      | Remove punctuation marks                         |
| remove_special_chars  | bool         | True      | Remove non-alphanumeric characters               |
| use_lemmatization     | bool         | True      | Apply lemmatization                              |
| use_stemming          | bool         | False     | Apply stemming instead of lemmatization          |
| stopwords_language    | str          | "english" | Language for stopwords                           |
| custom_stopwords      | list[str]    | None      | Add your own stopwords                           |
| remove_html_tags      | bool         | False     | Remove HTML tags                                 |
| remove_urls           | bool         | False     | Remove Urls                                      |


* Running Tests
```bash
pytest
```

### Why use this package?
There are other preprocessing tools (like NLTK or clean-text), but nlp-cleaner is designed to be:

1) Lightweight & Easy to Use → Just one class, minimal setup

2) Highly Configurable → Toggle lemmatization, stemming, number handling, punctuation, etc.

3) Production Ready → Clean and consistent outputs for ML pipelines

4) Customizable → Extend with your own stopwords or language models

5) Multi-language → Works beyond English when supported by spaCy/NLTK

If you want a plug-and-play solution to clean messy text quickly, this is the right tool.