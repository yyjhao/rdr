
from __future__ import print_function

from sqlalchemy import or_

import logging
import numpy as np
from optparse import OptionParser
import sys
from time import time
import matplotlib.pyplot as plt
import random
from urlparse import urlparse
from unidecode import unidecode

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import LinearSVC
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, MultinomialNB, GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.utils.extmath import density
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import BernoulliRBM
from sklearn import metrics

from base.models import Article
from base.database import db_session

from skynet.nlp_util import tokenizer

from pandas import DataFrame

use_hashing = False
print_report = True
n_features = 2 ** 16

categories = [
    "like",
    "pass",
]

# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


last_1k_articles = (
    db_session
    .query(Article)
    .filter(or_(Article.last_action == 'like', Article.last_action == 'pass'))
    .filter_by(user_id=1)
    .order_by(Article.last_action_timestamp.desc())
    .limit(2000)
    .all()
)


def build_data_frame(article):
    parsed_uri = urlparse(article.url)
    domain = parsed_uri.netloc
    return DataFrame({
        "class": [article.last_action],
        "origins": [[o.id for o in article.origins]],
        "domain": [domain],
        "title": [article.title],
        "article": [article],
    }, index=[article.id])


def gen_data_frame(data_set):
    result = DataFrame({'title': [], 'class': [], "domain": [], "origins": [], "article": []})
    for article in data_set:
        result = result.append(build_data_frame(article))

    return result.reindex(np.random.permutation(result.index))

# random.shuffle(last_1k_articles)
train_size = len(last_1k_articles) * 7 / 10
train_set = last_1k_articles[:train_size]
test_set = last_1k_articles[train_size:]

data_train = gen_data_frame(train_set)
data_test = gen_data_frame(test_set)

y_train, y_test = data_train['class'], data_test['class']

print("Extracting features from the training dataset using a sparse vectorizer")
if use_hashing:
    vectorizer = HashingVectorizer(stop_words='english', non_negative=True,
                                   preprocessor=lambda x: x,
                                   tokenizer=tokenizer,
                                   n_features=n_features)
    X_train = vectorizer.transform(data_train['article'])
else:
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5,
                                 preprocessor=lambda x: x,
                                 tokenizer=tokenizer,
                                 stop_words='english')
    X_train = vectorizer.fit_transform(data_train['article'])

print("Extracting features from the test dataset using the same vectorizer")
X_test = vectorizer.transform(data_test['article'])

# mapping from integer feature name to original token string
if use_hashing:
    feature_names = None
else:
    feature_names = np.asarray(vectorizer.get_feature_names())

###############################################################################
# Benchmark classifiers
def benchmark(clf):
    print('_' * 80)
    print("Training: ")
    print(clf)
    t0 = time()
    clf.fit(X_train, y_train)
    train_time = time() - t0
    print("train time: %0.3fs" % train_time)

    t0 = time()
    pred = clf.predict(X_test)
    test_time = time() - t0
    print("test time:  %0.3fs" % test_time)

    accuracy_score = metrics.accuracy_score(y_test, pred)
    print("Accuracy: {0}".format(accuracy_score))

    try:
        score = metrics.f1_score(y_test, pred)
        print("f1-score:   %0.3f" % score)
    except:
        print("Fuck!!!!!")
        score = 0

    if hasattr(clf, 'coef_'):
        print("dimensionality: %d" % clf.coef_.shape[1])
        print("density: %f" % density(clf.coef_))

        if feature_names is not None:
            print("top 10 keywords per class:")
            try:
                for i, category in enumerate(categories):
                    top10 = np.argsort(clf.coef_[i])[-10:]
                    print(("%s: %s"
                          % (category, " ".join(feature_names[top10]))))
            except:
                print("FUuuuuu")
        print()

    if print_report:
        print("classification report:")
        print(metrics.classification_report(y_test, pred,
                                            target_names=categories))

    clf_descr = str(clf).split('(')[0]
    return clf_descr, accuracy_score, train_time, test_time


results = []
for clf, name in (
        (RidgeClassifier(tol=1e-2, solver="lsqr"), "Ridge Classifier"),
        (Perceptron(n_iter=50), "Perceptron"),
        (PassiveAggressiveClassifier(n_iter=50), "Passive-Aggressive"),
        (KNeighborsClassifier(n_neighbors=10), "kNN")):
    print('=' * 80)
    print(name)
    results.append(benchmark(clf))

for penalty in ["l2", "l1"]:
    print('=' * 80)
    print("%s penalty" % penalty.upper())
    # Train Liblinear model
    results.append(benchmark(LinearSVC(loss='l2', penalty=penalty,
                                            dual=False, tol=1e-3)))

    # Train SGD model
    results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
                                           penalty=penalty)))

# Train SGD with Elastic Net penalty
print('=' * 80)
print("Elastic-Net penalty")
results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
                                       penalty="elasticnet")))

# Train NearestCentroid without threshold
print('=' * 80)
print("NearestCentroid (aka Rocchio classifier)")
results.append(benchmark(NearestCentroid()))

# Train sparse Naive Bayes classifiers
print('=' * 80)
print("Naive Bayes")
results.append(benchmark(MultinomialNB(alpha=.01)))
results.append(benchmark(BernoulliNB(alpha=.01)))

class L1LinearSVC(LinearSVC):

    def fit(self, X, y):
        # The smaller C, the stronger the regularization.
        # The more regularization, the more sparsity.
        self.transformer_ = LinearSVC(penalty="l1",
                                      dual=False, tol=1e-3)
        X = self.transformer_.fit_transform(X, y)
        return LinearSVC.fit(self, X, y)

    def predict(self, X):
        X = self.transformer_.transform(X)
        return LinearSVC.predict(self, X)

print('=' * 80)
print("LinearSVC with L1-based feature selection")
results.append(benchmark(L1LinearSVC()))


# make some plots

indices = np.arange(len(results))

results = [[x[i] for x in results] for i in range(4)]

clf_names, score, training_time, test_time = results
training_time = np.array(training_time) / np.max(training_time)
test_time = np.array(test_time) / np.max(test_time)

plt.figure(figsize=(12, 8))
plt.title("Score")
plt.barh(indices, score, .2, label="score", color='r')
plt.barh(indices + .3, training_time, .2, label="training time", color='g')
plt.barh(indices + .6, test_time, .2, label="test time", color='b')
plt.yticks(())
plt.legend(loc='best')
plt.subplots_adjust(left=.25)
plt.subplots_adjust(top=.95)
plt.subplots_adjust(bottom=.05)

for i, c in zip(indices, clf_names):
    plt.text(-.3, i, c)

plt.show()