import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize
from urllib.parse import urlparse
from unidecode import unidecode
import string
from nltk.util import ngrams

stemmer = nltk.stem.porter.PorterStemmer()
lemmatizer = nltk.stem.WordNetLemmatizer()
# stemmer = nltk.stem.snowball.EnglishStemmer()
exclude = set(
    list(string.punctuation) +
    nltk.corpus.stopwords.words('english') +
    [
        'also',
        'however',
        'n\'t',
    ])


def to_terms(text):
    text = text.lower()
    tokens = (word for sent in sent_tokenize(text) for word in word_tokenize(sent))
    return (stemmer.stem(lemmatizer.lemmatize(token)) for token in tokens if token not in exclude and len(token) > 2)


class Token(object):
    def __init__(self, info, data):
        self.info = info
        self.data = data

    def __gt__(self, token2):
        if self.info == token2.info:
            if self.info in ('title', 'summary'):
                if len(self.data) == len(token2.data):
                    for a, b in zip(self.data, token2.data):
                        if not a:
                            return False
                        elif not b:
                            return True
                        else:
                            return a > b
                else:
                    return len(self.data) > len(token2.data)
            else:
                return self.data > token2.data
        else:
            return self.info > token2.info

    def __hash__(self):
        return hash((self.info, self.data))

    def __eq__(self, token2):
        return self.info == token2.info and self.data == token2.data


def tokenizer(user_url):
    an_article = None
    for article in user_url.get_articles():
        an_article = article
        terms = list(to_terms(unidecode(article.title)))
        # bi = []
        bi = ngrams(terms, 2, pad_left=True, pad_right=True)
        # for term in list(bi):
        # for term in terms:
        for term in list(bi) + terms:
            # for term in list(tri) + list(bi) + terms:
            yield Token('title', term)
        if article.summary:
            terms = list(to_terms(BeautifulSoup(unidecode(article.summary)).get_text()))
            bi = ngrams(terms, 2, pad_left=True, pad_right=True)
            # for term in list(bi) + terms:
            for term in terms:
                yield Token('summary', term)
        yield Token('origin', article.origin)
    parsed_uri = urlparse(an_article.url)
    domain = parsed_uri.netloc
    yield Token('domain', domain)
