# tests/test_cleaner.py

import unittest
from nlp_text_clean.cleaner import TextCleaner


class TestTextCleaner(unittest.TestCase):

    def setUp(self):
        self.cleaner = TextCleaner(remove_numbers=True,
                                   remove_punctuation=True,
                                   use_lemmatization=True)

    def test_lowercase(self):
        text = "HELLO World"
        cleaned = self.cleaner.clean_text(text)
        self.assertIn("hello", cleaned)
        self.assertIn("world", cleaned)

    def test_remove_punctuation(self):
        text = "Hello, world!!!"
        cleaned = self.cleaner.clean_text(text)
        self.assertNotIn(",", cleaned)
        self.assertNotIn("!", cleaned)

    def test_remove_numbers(self):
        cleaner = TextCleaner(remove_numbers=True)
        text = "There are 123 apples"
        cleaned = cleaner.clean_text(text)
        self.assertNotIn("123", cleaned)

    def test_preserve_numbers_token(self):
        cleaner = TextCleaner(remove_numbers=True, preserve_num_token=True)
        text = "He scored 100 marks"
        cleaned = cleaner.clean_text(text)
        self.assertIn("<NUM>", cleaned)

    def test_stopwords_removal(self):
        text = "This is a test"
        cleaned = self.cleaner.clean_text(text)
        # "this", "is", "a" are stopwords in English
        self.assertEqual(cleaned, "test")

    def test_stemming(self):
        cleaner = TextCleaner(use_stemming=True, use_lemmatization=False)
        text = "running runs runner"
        cleaned = cleaner.clean_text(text)
        # Expect stemmed version
        self.assertIn("run", cleaned)

    def test_lemmatization(self):
        cleaner = TextCleaner(use_lemmatization=True)
        text = "running runs better"
        cleaned = cleaner.clean_text(text)
        self.assertIn("run", cleaned)  # lemmatized
        self.assertIn("well", cleaned)  # "better" lemmatized

    def test_custom_stopwords(self):
        cleaner = TextCleaner(custom_stopwords=["example"])
        text = "This is an example sentence"
        cleaned = cleaner.clean_text(text)
        self.assertNotIn("example", cleaned)
    
    def test_spanish_text(self):
        cleaner = TextCleaner(remove_punctuation=True, remove_numbers=True, preserve_num_token=True,language='spanish')
        text = "¡Hola! Esto es un ejemplo con 123 números."
        cleaned = cleaner.clean_text(text)
        print(cleaned)
        self.assertIn("hola", cleaned)
        self.assertIn("ejemplo", cleaned)
        self.assertNotIn("123", cleaned)
        self.assertNotIn("números", cleaned)  # "números" is a stopword in Spanish

    def test_remove_html_tags(self):
        cleaner = TextCleaner(remove_html_tags=True)
        text = "<p>Nagendra is a <b>nice</b> boy.</p>"
        cleaned = cleaner.clean_text(text)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("</p>", cleaned)
        self.assertNotIn("<b>", cleaned)
        self.assertNotIn("</b>", cleaned)
        self.assertIn("nagendra", cleaned)
        self.assertIn("nice", cleaned)
        self.assertIn("boy", cleaned)

    def test_remove_urls(self):
        cleaner = TextCleaner(remove_urls=True)
        text = "Visit https://www.example.com for more info."
        cleaned = cleaner.clean_text(text)
        self.assertNotIn("https://www.example.com", cleaned)
        self.assertIn("visit", cleaned)
        self.assertIn("info", cleaned)


if __name__ == "__main__":
    unittest.main()
