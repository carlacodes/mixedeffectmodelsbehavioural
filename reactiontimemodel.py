import sklearn.metrics
# from rpy2.robjects import pandas2ri
import seaborn as sns
from instruments.io.BehaviourIO import BehaviourDataSet
from sklearn.inspection import permutation_importance
from instruments.behaviouralAnalysis import reactionTimeAnalysis  # outputbehaviordf
from sklearn.preprocessing import MinMaxScaler
# from pymer4.models import Lmer
from pathlib import Path
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
import shap
import matplotlib
import lightgbm as lgb
import optuna
from optuna.integration import LightGBMPruningCallback
from sklearn.model_selection import StratifiedKFold
# scaler = MinMaxScaler()
import os
import xgboost as xgb
import matplotlib.pyplot as plt
# import rpy2.robjects.numpy2ri
import matplotlib.colors as mcolors
import sklearn
from sklearn.model_selection import train_test_split
from helpers.behaviouralhelpersformodels import *

def runlgbreleasetimes_for_a_ferret(data, paramsinput=None, ferret=1, ferret_name='F1815_Cruella'
                                    ):
    data = data[data['ferret'] == ferret]
    col = 'realRelReleaseTimes'
    dfx = data.loc[:, data.columns != col]
    col = 'ferret'
    dfx = dfx.loc[:, dfx.columns != col]

    X_train, X_test, y_train, y_test = train_test_split(dfx, data['realRelReleaseTimes'], test_size=0.2,
                                                        random_state=123)

    # param = {'max_depth': 2, 'eta': 1, 'objective': 'reg:squarederror'}
    # param['nthread'] = 4
    # param['eval_metric'] = 'auc'

    xg_reg = lgb.LGBMRegressor(random_state=123, verbose=1, **paramsinput)
    xg_reg.fit(X_train, y_train, verbose=1)
    ypred = xg_reg.predict(X_test)
    lgb.plot_importance(xg_reg)
    plt.title('feature importances for the LGBM Correct Release Times model for ferret ' + ferret_name)
    plt.show()

    kfold = KFold(n_splits=10)
    mse_train = cross_val_score(xg_reg, X_train, y_train, scoring='neg_mean_squared_error', cv=kfold)

    mse_test = mean_squared_error(ypred, y_test)
    print("MSE on test: %.4f" % (mse_test) + ferret_name)
    print("negative MSE training: %.2f%%" % (np.mean(mse_train) * 100.0))
    print(mse_train)
    shap_values = shap.TreeExplainer(xg_reg).shap_values(dfx)
    fig, ax = plt.subplots(figsize=(15, 15))
    # title kwargs still does nothing so need this workaround for summary plots
    shap.summary_plot(shap_values, dfx, show=False)
    fig, ax = plt.gcf(), plt.gca()
    plt.title('Ranked list of features over their impact in predicting reaction time for' + ferret_name)
    plt.xlabel('SHAP value (impact on model output) on reaction time' + ferret_name)

    labels = [item.get_text() for item in ax.get_yticklabels()]
    print(labels)
    trainandtestaccuracy ={
        'ferret': ferret_name,
        'mse_test': mse_test,
        'mse_train': mse_train,
        'mean_mse_train': np.mean(mse_train),
    }
    np.save('metrics/modelmse' + ferret_name + '.npy', trainandtestaccuracy)
    # labels[11] = 'distance to sensor'
    # labels[10] = 'target F0'
    # labels[9] = 'trial number'
    # labels[8] = 'precursor = target F0'
    # labels[7] = 'male talker'
    # labels[6] = 'time until target'
    # labels[5] = 'target F0 - precursor F0'
    # labels[4] = 'day of week'
    # labels[3] = 'precursor F0'
    # labels[2] = 'past trial was catch'
    # labels[1] = 'trial took place in AM'
    # labels[0] = 'past trial was correct'

    ax.set_yticklabels(labels)
    plt.savefig('figs/shap_summary_plot_correct_release_times_' + ferret_name + '.png', dpi=300, bbox_inches='tight')

    plt.show()

    shap.dependence_plot("timeToTarget", shap_values, dfx)  #

    explainer = shap.Explainer(xg_reg, X_train)
    shap_values2 = explainer(X_train)
    fig, ax = plt.subplots(figsize=(15, 15))
    shap.plots.scatter(shap_values2[:, "talker"], color=shap_values2[:, "precur_and_targ_same"])
    fig.tight_layout()

    plt.subplots_adjust(left=-10, right=0.5)

    plt.show()
    shap.plots.scatter(shap_values2[:, "pitchoftarg"], color=shap_values2[:, "talker"])
    plt.title('Reaction Time Model')
    plt.show()
    # logthe release times
    shap.plots.scatter(shap_values2[:, "trialNum"], color=shap_values2[:, "talker"],
                       title='Correct Responses - Reaction Time Model SHAP response \n vs. trial number for' + ferret_name)

    return xg_reg, ypred, y_test, results, mse_test



def runlgbreleasetimes(X, y, paramsinput=None):


    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.2,
                                                        random_state=42)

    # param = {'max_depth': 2, 'eta': 1, 'objective': 'reg:squarederror'}
    # param['nthread'] = 4
    # param['eval_metric'] = 'auc'

    xg_reg = lgb.LGBMRegressor(random_state=42, verbose=1, **paramsinput)
    # xg_reg = lgb.LGBMRegressor( colsample_bytree=0.3, learning_rate=0.1,
    #                           max_depth=10, alpha=10, n_estimators=10, random_state=42, verbose=1)


    xg_reg.fit(X_train, y_train, verbose=1)
    ypred = xg_reg.predict(X_test)
    lgb.plot_importance(xg_reg)
    plt.title('feature importances for the LGBM Correct Release Times model')
    plt.show()

    kfold = KFold(n_splits=10)
    results = cross_val_score(xg_reg, X_train, y_train, scoring='neg_mean_squared_error', cv=kfold)
    mse_train = mean_squared_error(ypred, y_test)

    mse = mean_squared_error(ypred, y_test)
    print("MSE on test: %.4f" % (mse))
    print("negative MSE training: %.2f%%" % (np.mean(results) * 100.0))
    print(results)
    shap_values = shap.TreeExplainer(xg_reg).shap_values(dfx)
    fig, ax = plt.subplots(figsize=(15, 15))
    # title kwargs still does nothing so need this workaround for summary plots
    shap.summary_plot(shap_values, dfx, show=False)
    fig, ax = plt.gcf(), plt.gca()
    plt.title('Ranked list of features over their impact in predicting reaction time')
    plt.xlabel('SHAP value (impact on model output) on reaction time')

    labels = [item.get_text() for item in ax.get_yticklabels()]
    print(labels)
    # labels[11] = 'distance to sensor'
    # labels[10] = 'target F0'
    # labels[9] = 'trial number'
    # labels[8] = 'precursor = target F0'
    # labels[7] = 'male talker'
    # labels[6] = 'time until target'
    # labels[5] = 'target F0 - precursor F0'
    # labels[4] = 'day of week'
    # labels[3] = 'precursor F0'
    # labels[2] = 'past trial was catch'
    # labels[1] = 'trial took place in AM'
    # labels[0] = 'past trial was correct'

    ax.set_yticklabels(labels)
    plt.savefig('figs/shapsummaryplot_allanimals2.png')

    plt.show()

    shap.dependence_plot("timeToTarget", shap_values, dfx)  #

    explainer = shap.Explainer(xg_reg, dfx)
    shap_values2 = explainer(dfx)
    fig, ax = plt.subplots(figsize=(15, 15))
    shap.plots.scatter(shap_values2[:, "talker"], color=shap_values2[:, "precur_and_targ_same"], show = False)
    fig.tight_layout()
    plt.savefig('figs/talkerprecurandtargsame_dependencyplot2.png')


    plt.subplots_adjust(left=-10, right=0.5)

    plt.show()
    shap.plots.scatter(shap_values2[:, "pitchoftarg"], color=shap_values2[:, "talker"], show = False)
    plt.title('Reaction Time Model')
    plt.show()
    # logthe release times
    shap.plots.scatter(shap_values2[:, "trialNum"], color=shap_values2[:, "talker"],
                       title='Correct Responses - Reaction Time Model SHAP response \n vs. trial number', show = False)
    fig, ax = plt.gcf(), plt.gca()

    plt.savefig('figs/reactiontimeversustrialnumber_dependencyplot.png')

    plt.show()

    shap.plots.scatter(shap_values2[:, "trialNum"], color=shap_values2[:, "talker"],
                       title='Correct Responses - Reaction Time Model SHAP response \n vs. trial number', show=False)
    fig, ax = plt.gcf(), plt.gca()
    plt.savefig('figs/reactiontimeversustrialnumber_dependencyplot2.png')

    plt.show()

    return xg_reg, ypred, y_test, results



def main():
    # study_release_times = run_optuna_study_releasetimes(dfx.to_numpy(), df_use[col].to_numpy())
    best_params = {'colsample_bytree': 0.49619263716341894,
     'alpha': 8.537376181435246,
     'n_estimators': 96,
     'learning_rate': 0.17871472565344848,
     'max_depth': 5,
     'bagging_fraction': 0.7000000000000001,
     'bagging_freq': 6}

    xg_reg, ypred, y_test, results = runlgbreleasetimes(dfx.to_numpy(), df_use[col].to_numpy(), paramsinput=best_params)