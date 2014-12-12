from base.models import Article, UserClassifier
from base.database import db_session

import skynet.nlp_util as nlp_util
from skynet.config import SCORE_DICT
import skynet.scikit_learn_util as scikit_learn_util
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

import nltk

import cPickle


class NaiveBayesClassifier():
    def __init__(self):
        self.classifier = None

    def train(self, train_set):
        article_features = [
            (nlp_util.gen_feature(a), a.last_action) for a in train_set
        ]

        self.classifier = nltk.NaiveBayesClassifier.train(article_features)

    def prob_classify(self, data):
        article_feature = nlp_util.gen_feature(data)
        prob_dist = self.classifier.prob_classify(article_feature)
        return {
            s: prob_dist.prob(s) for s in prob_dist.samples()
        }

    def dumps(self):
        return cPickle.dumps(self.classifier, -1)

    @classmethod
    def loads(cls, string):
        obj = cls()
        obj.classifier = cPickle.loads(string)
        return obj


class SVMClassifier():
    def __init__(self):
        self.classifier = None
        self.vectorizer = None

    def train(self, train_set):
        data_train = scikit_learn_util.gen_data_frame(train_set)
        self.vectorizer = CountVectorizer(
            preprocessor=lambda x: x,
            binary=True,
            tokenizer=nlp_util.tokenizer,
        )
        X_train = self.vectorizer.fit_transform(data_train['article'])
        self.classifier = SVC(probability=True, kernel="linear")
        # self.classifier.fit(X_train, data_train['last_action'], [1 if i == 'pass' else 10 for i in data_train['last_action']])
        self.classifier.fit(X_train, data_train['last_action'])

    def prob_classify(self, data):
        prob = self.classifier.predict_proba(self.vectorizer.transform([data]))[0]
        return {
            self.classifier.classes_[ind]: c for ind, c in enumerate(prob)
        }

    def dumps(self):
        return cPickle.dumps((self.classifier, self.vectorizer.vocabulary_), -1)

    @classmethod
    def loads(cls, string):
        obj = cls()
        stored = cPickle.loads(string)
        obj.classifier = stored[0]
        obj.vectorizer = CountVectorizer(
            preprocessor=lambda x: x,
            binary=True,
            tokenizer=nlp_util.tokenizer,
            vocabulary=stored[1]
        )
        return obj
