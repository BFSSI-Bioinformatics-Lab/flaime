import pickle

import lightgbm as lgb
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder

from flaim.classifiers.category_preprocessing import DataStore


class CategoryPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            self.model = None
            self.vectorizers = {}
            self.target_encoder = None
            self.model_version = None
        else:
            self.model, self.vectorizers, self.target_encoder, self.model_version = pickle.load(open(model_path, 'rb'))

    def train(self, ds: DataStore, process_names=True, process_ingredients=False):
        if process_names:
            self.vectorizers['name'] = CountVectorizer(max_features=1000, stop_words='english', analyzer='word',
                                                       strip_accents='ascii', dtype=int)
            name_matrix = self.vectorizers['name'].fit_transform(ds.names)
            column_names = self.vectorizers['name'].get_feature_names()
            names = pd.DataFrame.sparse.from_spmatrix(name_matrix, columns=column_names, index=ds.names.index)

            self.target_encoder = LabelEncoder()
            train = lgb.Dataset(pd.concat([ds.df, names], axis=1), self.target_encoder.fit_transform(ds.target))

            params = {
                'seed': 1,
                'objective': 'multiclass',
                'num_class': ds.target.nunique(),
                'metric': 'multi_error',
                'num_leaves': 7
            }

            self.model = lgb.train(params, train, num_boost_round=500, verbose_eval=50)
        # note: alternate models not yet added to module

    def predict(self, ds: DataStore, process=True):
        if 'name' in self.vectorizers:
            name_matrix = self.vectorizers['name'].transform(ds.names)
            column_names = self.vectorizers['name'].get_feature_names()
            names = pd.DataFrame.sparse.from_spmatrix(name_matrix, columns=column_names, index=ds.names.index)
            test = pd.concat([ds.df, names], axis=1)
        else:
            test = ds.df
        pred = self.model.predict(test)

        if process is False:
            return pred

        pred_name1 = pd.Series(self.target_encoder.inverse_transform(pred.argsort(axis=1)[..., -1]),
                               name='Pred 1', index=ds.df.index)
        pred_name2 = pd.Series(self.target_encoder.inverse_transform(pred.argsort(axis=1)[..., -2]),
                               name='Pred 2', index=ds.df.index)
        pred_name3 = pd.Series(self.target_encoder.inverse_transform(pred.argsort(axis=1)[..., -3]),
                               name='Pred 3', index=ds.df.index)

        sorted_pred = pred.copy()
        sorted_pred.sort(axis=1)

        confidence1 = pd.Series(sorted_pred[..., -1], name='Conf 1', index=ds.df.index)
        confidence2 = pd.Series(sorted_pred[..., -2], name='Conf 2', index=ds.df.index)
        confidence3 = pd.Series(sorted_pred[..., -3], name='Conf 3', index=ds.df.index)

        return pd.concat([pred_name1, confidence1, pred_name2, confidence2, pred_name3, confidence3],
                         axis=1, sort=False)

    def dump_model(self, model_path, model_version):
        pickle.dump((self.model, self.vectorizers, self.target_encoder, model_version), open(model_path, 'wb'))
