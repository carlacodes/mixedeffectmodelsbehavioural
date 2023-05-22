import sklearn.metrics
import seaborn as sns
from instruments.io.BehaviourIO import BehaviourDataSet
from sklearn.inspection import permutation_importance
from instruments.behaviouralAnalysis import reactionTimeAnalysis  # outputbehaviordf
from pathlib import Path
from sklearn.model_selection import cross_val_score
import shap
import matplotlib
import lightgbm as lgb
import optuna
from optuna.integration import LightGBMPruningCallback
from sklearn.model_selection import StratifiedKFold

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sklearn
from sklearn.model_selection import train_test_split
from helpers.behaviouralhelpersformodels import *
import sklearn.metrics as metrics
import random


# def objective(trial, X, y):
#     param_grid = {
#         "colsample_bytree": trial.suggest_float("colsample_bytree", 0.1, 1),
#         "subsample": trial.suggest_float("subsample", 0.1, 1),
#         "learning_rate": trial.suggest_float("learning_rate", 0.0001, 0.5),
#         "num_leaves": trial.suggest_int("num_leaves", 20, 500),
#         "max_depth": trial.suggest_int("max_depth", 3, 20),
#         "min_child_samples": trial.suggest_int("min_child_samples", 1, 200),
#         "reg_alpha": trial.suggest_float("reg_alpha", 0.1, 5),
#         "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 5),
#         "min_split_gain": trial.suggest_float("min_split_gain", 0, 20),
#         "bagging_freq": trial.suggest_int("bagging_freq", 1, 20),
#         "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1),
#         "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1, 5),
#     }
#
#     cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#
#     cv_scores = []
#     for idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
#         X_train, X_test = X[train_idx], X[test_idx]
#         y_train, y_test = y[train_idx], y[test_idx]
#
#         model = lgb.LGBMClassifier(objective="binary", random_state=42, **param_grid)
#         model.fit(
#             X_train,
#             y_train,
#             eval_set=[(X_test, y_test)],
#             eval_metric="binary_logloss",
#             early_stopping_rounds=100,
#             verbose=False,  # Set verbose to False to avoid printing evaluation results
#         )
#         preds = model.predict_proba(X_test)[:, 1]  # Use probabilities of the positive class
#         cv_scores.append(metrics.roc_auc_score(y_test, preds))
#
#     return -np.mean(cv_scores)
#
# Return negative mean CV score
def objective(trial, X, y):
    param_grid = {
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.1, 1),
        "subsample": trial.suggest_float("subsample", 0.1, 1),
        "learning_rate": trial.suggest_float("learning_rate", 0.0001, 0.5),
        "num_leaves": trial.suggest_int("num_leaves", 20, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_child_samples": trial.suggest_int("min_child_samples", 1, 200),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.1, 5),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 5),
        "min_split_gain": trial.suggest_float("min_split_gain", 0, 20),
        "bagging_freq": trial.suggest_int("bagging_freq", 1, 20),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1, 5),
        "min_child_weight": trial.suggest_float("min_child_weight", 0.001, 10),
        "max_bin": trial.suggest_int("max_bin", 100, 1000),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 200),
        "min_sum_hessian_in_leaf": trial.suggest_float("min_sum_hessian_in_leaf", 0.1, 50),
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_scores = []
    for idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = lgb.LGBMClassifier(objective="binary", random_state=42, **param_grid)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            eval_metric="binary_logloss",
            early_stopping_rounds=100,
            verbose=False,
        )
        preds = model.predict_proba(X_test)[:, 1]
        cv_scores.append(metrics.log_loss(y_test, preds))

    return np.mean(cv_scores)



def run_optuna_study_correctresp(X, y):
    study = optuna.create_study(direction="minimize", study_name="LGBM Classifier")
    func = lambda trial: objective(trial, X, y)
    study.optimize(func, n_trials=1000)
    print("Number of finished trials: ", len(study.trials))
    print(f"\tBest value of - auc: {study.best_value:.5f}")
    print(f"\tBest params:")

    for key, value in study.best_params.items():
        print(f"\t\t{key}: {value}")
    return study
def runlgbcorrectrespornotwithoptuna(dataframe, paramsinput=None, optimization = False, ferret_as_feature=False, one_ferret = False, ferrets = None):
    if ferret_as_feature == True:
        df_to_use = dataframe[["trialNum", "misslist", "talker", "side", "precur_and_targ_same",
                               "targTimes", "pastcorrectresp",
                               "pastcatchtrial", "ferret"]]
        labels = ['trial number','misslist', 'talker', 'audio side', 'precursor = target pitch','target presentation time', 'past response was correct', 'past trial was catch', 'ferret']
        df_to_use = df_to_use.rename(columns=dict(zip(df_to_use.columns, labels)))

        fig_dir = Path('D:/behavmodelfigs/correctresp_or_miss/ferret_as_feature')
        col = 'misslist'
        dfx = df_to_use.loc[:, df_to_use.columns != col]
        if optimization == False:
            # load the saved params
            paramsinput = np.load('../optuna_results/correctresponse_optunaparams_ferretasfeature_2105.npy', allow_pickle=True).item()
        else:
            study = run_optuna_study_correctresp(dfx.to_numpy(), df_to_use['misslist'].to_numpy())
            print(study.best_params)
            paramsinput = study.best_params
            np.save('../optuna_results/correctresponse_optunaparams_ferretasfeature_2105.npy', study.best_params)

    else:
        df_to_use =  dataframe[["trialNum", "misslist", "talker", "side", "precur_and_targ_same",
                           "targTimes","pastcorrectresp",
                           "pastcatchtrial"]]
        #
        labels = ['trial number','misslist', 'talker', 'audio side', 'precursor = target pitch','target presentation time', 'past response was correct', 'past trial was catch']
        df_to_use = df_to_use.rename(columns=dict(zip(df_to_use.columns, labels)))

        fig_dir = Path('D:/behavmodelfigs/correctresp_or_miss/')
        col = 'misslist'
        dfx = df_to_use.loc[:, df_to_use.columns != col]
        if optimization == False:
            # load the saved params
            if one_ferret:
                paramsinput = np.load('../optuna_results/correctresponse_optunaparams'+ferrets+'_2005.npy', allow_pickle=True).item()
            else:
                paramsinput = np.load('../optuna_results/correctresponse_optunaparams_2005_2.npy', allow_pickle=True).item()
        else:
            study = run_optuna_study_correctresp(dfx.to_numpy(), df_to_use['misslist'].to_numpy())
            print(study.best_params)
            paramsinput = study.best_params
            if one_ferret:
                np.save('../optuna_results/correctresponse_optunaparams_2005'+ferrets+'_2.npy', study.best_params)
            else:
                np.save('../optuna_results/correctresponse_optunaparams_2005_2.npy', study.best_params)


    X_train, X_test, y_train, y_test = train_test_split(dfx, df_to_use['misslist'], test_size=0.2, random_state=123)
    print(X_train.shape)
    print(X_test.shape)

    if ferret_as_feature:
        if one_ferret:

            fig_savedir = Path('D:/behavmodelfigs/correctresp_or_miss//ferret_as_feature/' + ferrets[0])
            if fig_savedir.exists():
                pass
            else:
                fig_savedir.mkdir(parents=True, exist_ok=True)
        else:
            fig_savedir = Path('D:/behavmodelfigs/correctresp_or_miss//ferret_as_feature')
    else:
        if one_ferret:

            fig_savedir = Path('D:/behavmodelfigs/correctresp_or_miss/'+ ferrets[0])
            if fig_savedir.exists():
                pass
            else:
                fig_savedir.mkdir(parents=True, exist_ok=True)
        else:
            fig_savedir = Path('D:/behavmodelfigs/correctresp_or_miss//')

    xg_reg = lgb.LGBMClassifier(objective="binary", random_state=123, **paramsinput)
    xg_reg.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="binary_logloss",
        early_stopping_rounds=100,
    )
    ypred = xg_reg.predict_proba(X_test)

    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=123)
    results = cross_val_score(xg_reg, X_test, y_test, scoring='accuracy', cv=kfold)
    bal_accuracy = cross_val_score(xg_reg, X_test, y_test, scoring='balanced_accuracy', cv=kfold)
    print("Accuracy: %.2f%%" % (np.mean(results) * 100.0))
    print(results)
    print('Balanced Accuracy: %.2f%%' % (np.mean(bal_accuracy) * 100.0))

    shap_values1 = shap.TreeExplainer(xg_reg).shap_values(dfx)


    custom_colors = ['gold',  'peru', "purple"]  # Add more colors as needed
    cmapcustom = mcolors.LinearSegmentedColormap.from_list('my_custom_cmap', custom_colors, N=1000)
    custom_colors_summary = ['peru', 'gold',]  # Add more colors as needed
    cmapsummary = matplotlib.colors.ListedColormap(custom_colors_summary)

    #elbow plot
    cumulative_importances_list = []
    for shap_values in shap_values1:
        feature_importances = np.abs(shap_values).sum(axis=0)
        cumulative_importances = np.cumsum(feature_importances)
        cumulative_importances_list.append(cumulative_importances)

    # Calculate the combined cumulative sum of feature importances
    cumulative_importances_combined = np.sum(cumulative_importances_list, axis=0)
    feature_labels = dfx.columns
    # Plot the elbow plot
    plt.figure(figsize=(10, 6))
    plt.plot(feature_labels, cumulative_importances_combined, marker='o', color = 'gold')
    plt.xlabel('Features')
    plt.ylabel('Cumulative Feature Importance')
    plt.title('Elbow Plot of Cumulative Feature Importance for Miss Model')
    plt.xticks(rotation=45, ha='right')  # rotate x-axis labels for better readability
    plt.savefig(fig_dir / 'elbowplot.png', dpi=500, bbox_inches='tight')
    plt.show()

    shap.summary_plot(shap_values1, X_train, show = False, color=cmapsummary)
    fig, ax = plt.gcf(), plt.gca()
    plt.title('Ranked list of features over their \n impact in predicting a miss', fontsize = 18)
    # Get the plot's Patch objects
    labels = [item.get_text() for item in ax.get_yticklabels()]
    # print(labels)
    # labels[12] = 'side of audio presentation'
    # labels[11] = 'trial number'
    # labels[10] = 'precursor = target pitch'
    # labels[9] = 'target presentation time'
    # labels[8] = 'pitch of target'
    # labels[7] = 'session occured in the morning'
    # labels[6] = 'cosine similarity'
    # labels[5] = 'past trial was catch'
    # labels[4] = 'precursor pitch = target pitch'
    # labels[3] = 'past trial was correct'
    # labels[2] = 'pitch change'
    # labels[1] = 'Days since start of week'
    # labels[0] = 'talker'
    # # ax.set_yticklabels(labels)
    fig.tight_layout()
    plt.savefig(fig_dir / 'shap_summary_correctresp.png', dpi=1000, bbox_inches = "tight")

    shap.dependence_plot("precursor = target pitch", shap_values1[0], dfx)  #
    plt.show()

    result = permutation_importance(xg_reg, X_test, y_test, n_repeats=100,
                                    random_state=123, n_jobs=2)
    sorted_idx = result.importances_mean.argsort()
    fig, ax = plt.subplots()
    ax.barh(X_test.columns[sorted_idx], result.importances[sorted_idx].mean(axis=1).T, color = 'peru')
    ax.set_title("Permutation importances on predicting a miss")
    fig.tight_layout()
    plt.savefig(fig_dir / 'permutation_importance.png', dpi=500)
    plt.show()


    explainer = shap.Explainer(xg_reg, X_train, feature_names=X_train.columns)
    shap_values2 = explainer(X_train)

    fig, ax = plt.subplots()
    shap.plots.scatter(shap_values2[:, "trial number"], color=shap_values2[:, "precursor = target pitch"], ax=ax, cmap = cmapcustom, show = False)
    fig, ax = plt.gcf(), plt.gca()
    cb_ax = fig.axes[1]
    # Modifying color bar parameters
    cb_ax.tick_params(labelsize=15)
    # cb_ax.set_yticks([1, 2, 3,4, 5])
    # cb_ax.set_yticklabels(['109', '124', '144', '191', '251'])
    cb_ax.set_ylabel("precursor = target pitch", fontsize=15)
    plt.title('Trial number and its effect on the \n miss probability', fontsize = 18)
    plt.xlabel('Trial number', fontsize = 15)
    plt.ylabel('SHAP value', fontsize = 15)
    plt.savefig( fig_dir / 'trialnum_vs_precurpitch.png', dpi=1000, bbox_inches = "tight")
    plt.show()

    fig, ax = plt.subplots(figsize=(10, 10))
    shap.plots.scatter(shap_values2[:, "audio side"], color=shap_values2[:, "precursor = target pitch"], ax=ax, cmap = cmapcustom, show = False)
    fig, ax = plt.gcf(), plt.gca()
    cb_ax = fig.axes[1]
    # Modifying color bar parameters
    cb_ax.tick_params(labelsize=15)
    cb_ax.set_ylabel("precursor = target pitch word", fontsize=15)

    plt.xticks([0, 1 ], labels = ['left', 'right'], fontsize =15)
    plt.ylabel('SHAP value', fontsize=10)
    plt.title('Pitch of the side of the booth \n versus impact in miss probability', fontsize=18)
    plt.ylabel('SHAP value', fontsize=16)
    plt.xlabel('Side of audio presentation', fontsize=16)
    plt.savefig(fig_dir / 'side_vs_precurpitch.png', dpi=1000, bbox_inches = "tight")
    plt.show()


    fig, ax = plt.subplots(figsize=(10, 10))
    shap.plots.scatter(shap_values2[:, "precursor = target pitch"], color=shap_values2[:, "trial number"], ax=ax, cmap = cmapcustom, show = False)
    fig, ax = plt.gcf(), plt.gca()
    cb_ax = fig.axes[1]
    # Modifying color bar parameters
    cb_ax.tick_params(labelsize=15)
    cb_ax.set_ylabel("precursor = target pitch word", fontsize=15)

    plt.xticks([0, 1 ], labels = ['Precursor = target F0', ' Precursor ≠ target F0'], fontsize =15)
    plt.ylabel('SHAP value', fontsize=10)
    plt.title('Precusor = target F0 \n versus impact in miss probability', fontsize=18)
    plt.ylabel('SHAP value', fontsize=16)
    plt.xlabel('Side of audio presentation', fontsize=16)
    plt.savefig(fig_dir / 'precursortargpitchintrialnumber.png', dpi=1000, bbox_inches = "tight")
    plt.show()
    #
    # shap.plots.scatter(shap_values2[:, "pitch of target"], color=shap_values2[:, "precursor = target pitch"], show=False, cmap = cmapcustom)
    # fig, ax = plt.gcf(), plt.gca()
    # # Get colorbar
    # cb_ax = fig.axes[1]
    # # Modifying color bar parameters
    # cb_ax.tick_params(labelsize=15)
    # cb_ax.set_yticks([1, 2, 3,4, 5])
    # # cb_ax.set_yticklabels(['109', '124', '144', '191', '251'])
    # cb_ax.set_ylabel("precursor = target pitch", fontsize=12)
    # # cb_ax.set_yticklabels( ['109 Hz', '124 Hz', '144 Hz', '191 Hz', '251 Hz'], fontsize=15)
    # plt.ylabel('SHAP value', fontsize=10)
    # plt.title('Pitch of target \n versus impact in miss probability', fontsize=18)
    # plt.ylabel('SHAP value', fontsize=16)
    # plt.xlabel('Pitch of target (Hz)', fontsize=16)
    # # plt.xticks([1,2,3,4,5], labels=['109', '124', '144 ', '191', '251'], fontsize=15)
    # plt.show()


    shap.plots.scatter(shap_values2[:, "precursor = target pitch"], color=shap_values2[:, "talker"])
    plt.show()
    shap.plots.scatter(shap_values2[:, "trial number"], color=shap_values2[:, "talker"], show=False)
    plt.title('trial number \n vs. SHAP value impact')
    plt.ylabel('SHAP value', fontsize=18)
    plt.show()

    shap.plots.scatter(shap_values2[:, "trial number"], color=shap_values2[:, "target presentation time"], show=False)
    plt.title('Trial number versus SHAP value for miss probability, \n colored by target presentation time', fontsize=18)
    plt.ylabel('SHAP value', fontsize=18)
    plt.xlabel('Trial number', fontsize=15)
    plt.show()

    shap.plots.scatter(shap_values2[:, "target presentation time"], color=shap_values2[:, "trial number"], show=False)
    plt.title('target presentation time versus SHAP value for miss probability, \n colored by trial number', fontsize=18)
    plt.ylabel('SHAP value', fontsize=18)
    plt.xlabel('Target presentation time', fontsize=15)
    plt.show()

    fig, ax = plt.subplots(figsize=(15, 35))
    shap.plots.scatter(shap_values2[:, "audio side"], color=shap_values2[:, "trial number"], show=False)
    plt.title('SHAP values as a function of the side of the audio, \n coloured by the trial number', fontsize=18)
    plt.ylabel('SHAP value', fontsize=18)
    plt.xticks([0, 1], ['Left', 'Right'], fontsize=18)
    plt.show()

    fig, ax = plt.subplots(figsize=(15, 55))
    shap.plots.scatter(shap_values2[:, "precursor = target pitch"], color=shap_values2[:, "trial number"], show=False)
    plt.title('SHAP values as a function of the pitch of the target, \n coloured by the target presentation time',
              fontsize=18)
    plt.ylabel('SHAP value', fontsize=18)
    plt.xlabel('Pitch of target', fontsize=12)
    # plt.xticks([1, 2, 3, 4, 5], ['109 Hz', '124 Hz', '144 Hz', '191 Hz', '251 Hz'], fontsize=18)
    plt.show()

    return xg_reg, ypred, y_test, results, shap_values1, X_train, y_train, bal_accuracy, shap_values2





def reservoir_sampling_dataframe(df, k):
    reservoir = []
    n = 0
    for index, row in df.iterrows():
        n += 1
        if len(reservoir) < k:
            reservoir.append(row.copy())
        else:
            # Randomly replace rows in the reservoir with decreasing probability
            replace_index = random.randint(0, n - 1)
            if replace_index < k:
                reservoir[replace_index] = row.copy()

    # Create a new DataFrame from the reservoir
    sampled_df = pd.DataFrame(reservoir)

    return sampled_df

def run_correct_responsepipeline(ferrets):
    resultingcr_df = behaviouralhelperscg.get_df_behav(ferrets=ferrets, includefaandmiss=False, includemissonly=True, startdate='04-01-2020',
                                  finishdate='03-01-2023')
    filepath = Path('D:/dfformixedmodels/correctresponsemodel_dfuse.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    resultingcr_df.to_csv(filepath)

    # df_pitchtargsame = resultingcr_df[resultingcr_df['precur_and_targ_same'] == 1]
    # df_pitchtargdiff = resultingcr_df[resultingcr_df['precur_and_targ_same'] == 0]
    # if len(df_pitchtargsame) > len(df_pitchtargdiff)*1.2:
    #     df_pitchtargsame = df_pitchtargsame.sample(n=len(df_pitchtargdiff), random_state=123)
    # elif len(df_pitchtargdiff) > len(df_pitchtargsame)*1.2:
    #     df_pitchtargdiff = df_pitchtargdiff.sample(n=len(df_pitchtargsame), random_state=123)
    # resultingcr_df = pd.concat([df_pitchtargsame, df_pitchtargdiff], axis = 0)


    df_intra = resultingcr_df[resultingcr_df['intra_trial_roving'] == 1]
    df_inter = resultingcr_df[resultingcr_df['inter_trial_roving'] == 1]
    df_control = resultingcr_df[resultingcr_df['control_trial'] == 1]

    if len(df_intra) > len(df_inter)*1.2:
        df_intra = df_intra.sample(n=len(df_inter), random_state=123)
    elif len(df_inter) > len(df_intra)*1.2:
        df_inter = df_inter.sample(n=len(df_intra), random_state=123)

    if len(df_control) > len(df_intra)*1.2:
        df_control = df_control.sample(n=len(df_intra), random_state=123)
    elif len(df_control) > len(df_inter)*1.2:
        df_control = df_control.sample(n=len(df_inter), random_state=123)

    resultingcr_df = pd.concat([df_control, df_intra, df_inter], axis=0)


    df_miss = resultingcr_df[resultingcr_df['misslist'] == 1]
    df_nomiss = resultingcr_df[resultingcr_df['misslist'] == 0]

    if len(df_nomiss) > len(df_miss)*1.2:
        df_nomiss = df_nomiss.sample(n=len(df_miss), random_state=123)
    elif len(df_miss) > len(df_nomiss)*1.2:
        df_miss = df_miss.sample(n=len(df_nomiss), random_state=123)

    resultingcr_df = pd.concat([df_nomiss, df_miss], axis=0)

    # #
    # #shuffle the rows
    # resultingcr_df = resultingcr_df.sample(frac=1).reset_index(drop=True)




    if len(ferrets) == 1:
        one_ferret = True
        ferret_as_feature = False
    else:
        one_ferret = False
        ferret_as_feature = True

    xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2 = runlgbcorrectrespornotwithoptuna(
        resultingcr_df, optimization=False, ferret_as_feature = ferret_as_feature, one_ferret=one_ferret, ferrets=ferrets)
    return xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2


# def test_function(ferrets):
#     resultingcr_df = behaviouralhelperscg.get_df_behav(ferrets=ferrets, includefaandmiss=False, includemissonly=True, startdate='04-01-2020',
#                                   finishdate='03-01-2023')
#     filepath = Path('D:/dfformixedmodels/correctresponsemodel_dfuse.csv')
#     filepath.parent.mkdir(parents=True, exist_ok=True)
#     resultingcr_df.to_csv(filepath)
#     xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2 = runlgbcorrectrespornotwithoptuna(
#         resultingcr_df, optimization=True, ferret_as_feature=True)
#     return xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2

def run_models_for_all_or_one_ferret(run_individual_ferret_models):
    if run_individual_ferret_models:
        ferrets = ['F1702_Zola', 'F1815_Cruella', 'F1803_Tina', 'F2002_Macaroni', 'F2105_Clove']
        ferrets = ['F1702_Zola', 'F1815_Cruella', 'F1803_Tina', 'F2002_Macaroni', 'F2105_Clove']
        for ferret in ferrets:
            xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2 = run_correct_responsepipeline(
                ferrets = [ferret])
    else:
        xg_reg2, ypred2, y_test2, results2, shap_values, X_train, y_train, bal_accuracy, shap_values2 = run_correct_responsepipeline(
            ['F1702_Zola', 'F1815_Cruella', 'F1803_Tina', 'F2002_Macaroni', 'F2105_Clove'])

if __name__ == '__main__':
    run_models_for_all_or_one_ferret(run_individual_ferret_models=False)
