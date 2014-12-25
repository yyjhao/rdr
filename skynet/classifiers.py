import skynet.nlp_util as nlp_util
import skynet.scikit_learn_util as scikit_learn_util
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

import pickle


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
        self.classifier.fit(X_train, data_train['last_action'])

    def prob_classify(self, data):
        prob = self.classifier.predict_proba(self.vectorizer.transform([data]))[0]
        return {
            self.classifier.classes_[ind]: c for ind, c in enumerate(prob)
        }

    def dumps(self):
        return pickle.dumps((self.classifier, self.vectorizer.vocabulary_), -1)

    @classmethod
    def loads(cls, string):
        obj = cls()
        stored = pickle.loads(string)
        obj.classifier = stored[0]
        obj.vectorizer = CountVectorizer(
            preprocessor=lambda x: x,
            binary=True,
            tokenizer=nlp_util.tokenizer,
            vocabulary=stored[1]
        )
        return obj
