import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize
from urlparse import urlparse
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

def gen_feature(article):
    features = {}
    terms = list(to_terms(unidecode(article.title)))
    # bi = []
    bi = ngrams(terms, 2, pad_left=True, pad_right=True)
    for term in list(bi):
    # for term in list(bi) + terms:
        features[(term, 'title')] = True
    if article.summary and False:
        terms = list(to_terms(BeautifulSoup(unidecode(article.summary)).get_text()))
        bi = ngrams(terms, 2, pad_left=True, pad_right=True)
        # for term in list(bi) + terms:
        for term in terms:
            features[(term, 'summary')] = True
    features['origin_count'] = len(article.origins)
    for origin in article.origins:
        features[(origin.id, 'origin')] = True
    parsed_uri = urlparse(article.url)
    domain = parsed_uri.netloc
    features['domain'] = domain

    return features