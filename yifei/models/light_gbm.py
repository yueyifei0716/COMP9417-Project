import lightgbm as lgb
from hyperopt import hp, fmin, tpe
from feature import feature_select_pearson
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from numpy.random import RandomState
from sklearn.metrics import mean_squared_error


def params_append(params):
    """
    动态回调参数函数，params视作字典
    :param params:lgb参数字典
    :return params:修正后的lgb参数字典
    """
    params['feature_pre_filter'] = False
    params['objective'] = 'regression'
    params['metric'] = 'rmse'
    params['bagging_seed'] = 2020
    return params


def param_hyperopt(train):
    """
    模型参数搜索与优化函数
    :param train:训练数据集
    :return params_best:lgb最优参数
    """
    # Part 1.划分特征名称，删除ID列和标签列
    label = 'target'
    features = train.columns.tolist()
    features.remove('card_id')
    features.remove('target')

    # Part 2.封装训练数据
    train_data = lgb.Dataset(train[features], train[label])

    # Part 3.内部函数，输入模型超参数损失值输出函数
    def hyperopt_objective(params):
        """
        输入超参数，输出对应损失值
        :param params:
        :return:最小rmse
        """
        # 创建参数集
        params = params_append(params)
        print(params)

        # 借助lgb的cv过程，输出某一组超参数下损失值的最小值
        res = lgb.cv(params, train_data, 1000,
                     nfold=2,
                     stratified=False,
                     shuffle=True,
                     metrics='rmse',
                     early_stopping_rounds=20,
                     verbose_eval=False,
                     show_stdv=False,
                     seed=2020)
        return min(res['rmse-mean'])  # res是个字典

    # Part 4.lgb超参数空间
    # params_space = {
    #     'learning_rate': hp.uniform('learning_rate', 1e-2, 5e-1),
    #     'bagging_fraction': hp.uniform('bagging_fraction', 0.5, 1),
    #     'feature_fraction': hp.uniform('feature_fraction', 0.5, 1),
    #     'num_leaves': hp.choice('num_leaves', list(range(10, 300, 10))),
    #     'reg_alpha': hp.randint('reg_alpha', 0, 10),
    #     'reg_lambda': hp.uniform('reg_lambda', 0, 10),
    #     'bagging_freq': hp.randint('bagging_freq', 1, 10),
    #     'min_child_samples': hp.choice('min_child_samples', list(range(1, 30, 5)))
    # }
    params_space = {
        'bagging_fraction': 0.9022336069269954,
        'bagging_freq': 2,
        'feature_fraction': 0.9373662317255621,
        'learning_rate': 0.014947332175194025,
        'min_child_samples': 5,
        'num_leaves': 7,
        'reg_alpha': 2,
        'reg_lambda': 3.5907566887206896
    }

    # Part 5.TPE超参数搜索
    params_best = fmin(
        hyperopt_objective,
        space=params_space,
        algo=tpe.suggest,
        max_evals=30,
        rstate=np.random.default_rng(2020))

    # 返回最佳参数
    return params_best


train = pd.read_csv("../preprocess/train.csv")
test = pd.read_csv("../preprocess/test.csv")
train, test = feature_select_pearson(train, test)
best_clf = param_hyperopt(train)

print(best_clf)

# 再次申明固定参数
best_clf = params_append(best_clf)

# 数据准备过程
label = 'target'
features = train.columns.tolist()
features.remove('card_id')
features.remove('target')

# 数据封装
lgb_train = lgb.Dataset(train[features], train[label])
# 在全部数据集上训练模型
bst = lgb.train(best_clf, lgb_train)
# # 在测试集上完成预测
# bst.predict(train[features])
# 简单查看训练集RMSE
print('The score is:')
print(np.sqrt(mean_squared_error(train[label].values, bst.predict(train[features]))))