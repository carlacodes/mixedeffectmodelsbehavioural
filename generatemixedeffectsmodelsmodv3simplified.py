import click
import sklearn.metrics
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

import instruments
from instruments.io.BehaviourIO import BehaviourDataSet, WeekBehaviourDataSet
from instruments.config import behaviouralDataPath, behaviourOutput
from instruments.behaviouralAnalysis import createWeekBehaviourFigs, reactionTimeAnalysis  # outputbehaviordf
import math
from time import time
from pymer4.models import Lmer
from sklearn.feature_selection import RFE
from sklearn.svm import SVR
from sklearn.preprocessing import MinMaxScaler
from pymer4.models import Lmer

scaler = MinMaxScaler()
import os
import matplotlib.pyplot as plt
from instruments.helpers.extract_helpers import extractAllFerretData
import pandas as pd
import numpy as np
import rpy2.robjects.numpy2ri
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri

from rpy2.robjects.conversion import localconverter

rpy2.robjects.numpy2ri.activate()
from rpy2.robjects.packages import importr

# import R's "base" package
base = importr('base')
easystats = importr('easystats')
performance = importr('performance')
rstats = importr('stats')


def cli_behaviour_week(path=None,
                       output=None,
                       ferrets=None,
                       day=None):
    if output is None:
        output = behaviourOutput

    if path is None:
        path = behaviouralDataPath

    dataSet = WeekBehaviourDataSet(filepath=path,
                                   outDir=output,
                                   ferrets=ferrets,
                                   day=day)

    if ferrets is not None:
        ferrets = [ferrets]
    else:
        ferrets = [ferret for ferret in next(os.walk(db_path))[1] if ferret.startswith('F')]

    allData = dataSet._load()
    for ferret in ferrets:
        ferretFigs = createWeekBehaviourFigs(allData, ferret)
        dataSet._save(figs=ferretFigs)


#
# cli.add_command(cli_behaviour_week)


# @click.command(name='reaction_time')
# @click.option('--path', '-p', type=click.Path(exists=True))
# @click.option('--output', '-o', type=click.Path(exists=False))
# @click.option('--ferrets', '-f', default=None)
# @click.option('--startdate', '-sta', default=None)
# @click.option('--finishdate', '-sto', default=None)
def cli_reaction_time(path=None,
                      output=None,
                      ferrets=None,
                      startdate=None,
                      finishdate=None):
    if output is None:
        output = behaviourOutput

    if path is None:
        path = behaviouralDataPath

    #    if ferrets is not None:
    #        ferrets = [ferrets]
    #    else:
    #        ferrets = [ferret for ferret in next(os.walk(db_path))[1] if ferret.startswith('F')]

    dataSet = BehaviourDataSet(filepath=path,
                               startDate=startdate,
                               finishDate=finishdate,
                               ferrets=ferrets,
                               outDir=output)

    allData = dataSet._load()
    # for ferret in ferrets:
    ferret = ferrets
    ferrData = allData.loc[allData.ferretname == ferret]
    # if ferret == 'F1702_Zola':
    #     ferrData = ferrData.loc[(ferrData.dates != '2021-10-04 10:25:00')]

    ferretFigs = reactionTimeAnalysis(ferrData)
    dataSet._save(figs=ferretFigs, file_name='reaction_times_{}_{}_{}.pdf'.format(ferret, startdate, finishdate))


def get_df_behav(path=None,
                 output=None,
                 ferrets=None,
                 includefaandmiss=False,
                 startdate=None,
                 finishdate=None):
    if output is None:
        output = behaviourOutput

    if path is None:
        path = behaviouralDataPath


    allData, ferrets = extractAllFerretData(ferrets, path, startDate=startdate,
                                            finishDate=finishdate)
    fs = 24414.062500
    bigdata = pd.DataFrame()
    numofferrets = allData['ferret'].unique()
    for ferret in numofferrets:
        print(ferret)
        # newdata = allData.iloc(allData['ferret'] == ferret)
        newdata = allData[allData['ferret'] == ferret]
        # newdata = allData['absentTime'][0]
        newdata['targTimes'] = newdata['timeToTarget'] / fs

        newdata['centreRelease'] = newdata['lickRelease'] - newdata['startTrialLick']
        newdata['relReleaseTimes'] = newdata['centreRelease'] - newdata['targTimes']
        newdata['realRelReleaseTimes'] = newdata['relReleaseTimes'] - newdata['absentTime']

        distractors = newdata['distractors']
        talkermat = {}
        talkerlist = newdata['talker']

        for i0 in range(0, len(distractors)):
            talkermat[i0] = int(talkerlist.values[i0]) * np.ones(len(distractors.values[i0]))
        talkermat = pd.Series(talkermat, index=talkermat.keys())

        pitchshiftmat = newdata['PitchShiftMat']
        # if len(pitchshiftmat) == 0:
        #     pitchshiftmat = talkermat  # make array equivalent to size of pitch shift mat just like talker [3,3,3,3] # if this is inter trial roving then talker is the pitch shift

        # except:
        #     pitchshiftmat = talkermat  # make array equivalent to size of pitch shift mat just like talker [3,3,3,3] # if this is inter trial roving then talker is the pitch shift
        precursorlist = newdata['distractors']
        catchtriallist = newdata['catchTrial']
        chosenresponse = newdata['response']
        realrelreleasetimelist = newdata['realRelReleaseTimes']
        pitchoftarg = np.empty(len(pitchshiftmat))
        pitchofprecur = np.empty(len(pitchshiftmat) )
        stepval = np.empty(len(pitchshiftmat) )
        gradinpitch = np.empty(len(pitchshiftmat))
        gradinpitchprecur = np.empty(len(pitchshiftmat))
        timetotarglist = np.empty(len(pitchshiftmat))

        precur_and_targ_same = np.empty(len(pitchshiftmat))
        talkerlist2 = np.empty(len(pitchshiftmat))

        correctresp = np.empty(shape=(0, 0))
        pastcorrectresp = np.empty(shape=(0, 0))
        pastcatchtrial = np.empty(shape=(0, 0))
        droplist = np.empty(shape=(0, 0))
        droplistnew = np.empty(shape=(0, 0))
        print(len(newdata['realRelReleaseTimes'].values))

        for i in range(1, len(newdata['realRelReleaseTimes'].values)):
            chosenresponseindex = chosenresponse.values[i]
            pastcatchtrialindex = catchtriallist.values[i - 1]

            realrelreleasetime = realrelreleasetimelist.values[i]
            pastrealrelreleasetime = realrelreleasetimelist.values[i - 1]
            pastresponseindex = chosenresponse.values[(i - 1)]
            chosentrial = pitchshiftmat.values[i]
            if isinstance(chosentrial, float):
                chosentrial = talkermat.values[i]
            chosendisttrial = precursorlist.values[i]
            chosentalker = talkerlist.values[i]
            if chosentalker == 3:
                chosentalker = 1
            if chosentalker == 8:
                chosentalker = 2
            if chosentalker == 13:
                chosentalker = 2
            if chosentalker == 5:
                chosentalker = 1
            talkerlist2[i] = chosentalker

            targpos = np.where(chosendisttrial == 1)
            if ((
                        chosenresponseindex == 0 or chosenresponseindex == 1) and realrelreleasetime >= 0) or chosenresponseindex == 3:
                correctresp = np.append(correctresp, 1)
            else:
                correctresp = np.append(correctresp, 0)
            if ((pastresponseindex == 0 or pastresponseindex == 1) and pastrealrelreleasetime >= 0) or pastresponseindex == 3:
                pastcorrectresp = np.append(pastcorrectresp, 1)
            else:
                pastcorrectresp = np.append(pastcorrectresp, 0)

            if pastcatchtrialindex == 1:
                pastcatchtrial = np.append(pastcatchtrial, 1)
            else:
                pastcatchtrial = np.append(pastcatchtrial, 0)
            try:
                if chosentrial[targpos[0]] == 8.0:
                    pitchoftarg[i] == 3.0
                else:
                    pitchoftarg[i] = chosentrial[targpos[0]]

                if chosentrial[targpos[0] - 1] == 8.0:
                    pitchofprecur[i] == 3.0
                else:
                    pitchofprecur[i] = chosentrial[targpos[0] - 1]
                    # 1 is 191, 2 is 124, 3 is 144hz female, 5 is 251, 8 is 144hz male, 13 is109hz male
                    # pitchof targ 1 is 124hz male, pitchoftarg4 is 109Hz Male

                if chosentrial[targpos[0] - 1] == 3.0:
                    stepval[i] = 1.0
                elif chosentrial[targpos[0] - 1] == 8.0:
                    stepval[i] = 2.0
                elif chosentrial[targpos[0] - 1] == 13.0:
                    stepval[i] = 1.0
                elif chosentrial[targpos[0] - 1] == 5.0:
                    stepval[i] = 1.0
                else:
                    stepval[i] = 0.0

                if pitchoftarg[i] == pitchofprecur[i]:
                    precur_and_targ_same[i] = 1
                else:
                    precur_and_targ_same[i] = 0


            except:
                print(len(newdata))
                indexdrop = newdata.iloc[i].name
                droplist = np.append(droplist, i)
                droplistnew = np.append(droplistnew, indexdrop)
                continue
        #newdata.drop(0, axis=0, inplace=True)  # drop first trial for each animal
        newdata.drop(index=newdata.index[0],
                axis=0,
                inplace=True)
        newdata.drop(droplistnew, axis=0, inplace=True)

        # TODO: CHECK IF DATA IS EXTRACTED SEQUENTIALLY SO TRIAL NUMS ARE CONCATENATED CORRECTLY
        droplist = [int(x) for x in droplist]  # drop corrupted metdata trials

        pitchoftarg = pitchoftarg[~np.isnan(pitchoftarg)]
        pitchoftarg = pitchoftarg.astype(int)
        gradinpitch = gradinpitch[~np.isnan(gradinpitch)]

        correctresp = correctresp[~np.isnan(correctresp)]
        pastcorrectresp = pastcorrectresp[~np.isnan(pastcorrectresp)]

        pastcatchtrial = pastcatchtrial[~np.isnan(pastcatchtrial)]

        pitchoftarg = np.delete(pitchoftarg, 0)
        talkerlist2 = np.delete(talkerlist2, 0)
        stepval = np.delete(stepval, 0)
        pitchofprecur = np.delete(pitchofprecur, 0)
        precur_and_targ_same = np.delete(precur_and_targ_same, 0)

        pitchoftarg = np.delete(pitchoftarg, droplist)
        talkerlist2 = np.delete(talkerlist2, droplist)
        stepval = np.delete(stepval, droplist)

        newdata['pitchoftarg'] = pitchoftarg.tolist()

        pitchofprecur = np.delete(pitchofprecur, droplist)
        newdata['pitchofprecur'] = pitchofprecur.tolist()

        correctresp = np.delete(correctresp, droplist)
        pastcorrectresp = np.delete(pastcorrectresp, droplist)
        pastcatchtrial = np.delete(pastcatchtrial, droplist)

        precur_and_targ_same = np.delete(precur_and_targ_same, droplist)

        correctresp = correctresp.astype(int)
        pastcatchtrial = pastcatchtrial.astype(int)
        pastcorrectresp = pastcorrectresp.astype(int)

        newdata['correctresp'] = correctresp.tolist()
        print(len(pastcorrectresp))
        print(len(correctresp))
        newdata['pastcorrectresp'] = pastcorrectresp.tolist()
        newdata['talker'] = talkerlist2.tolist()
        newdata['pastcatchtrial'] = pastcatchtrial.tolist()
        newdata['stepval'] = stepval.tolist()
        precur_and_targ_same = precur_and_targ_same.astype(int)
        newdata['precur_and_targ_same'] = precur_and_targ_same.tolist()
        newdata['timeToTarget'] = newdata['timeToTarget'] / 24414.0625
        newdata['AM'] = newdata['AM'].astype(int)
        newdata['talker'] = newdata['talker'] - 1
        # optionvector=[1 3 5];, male optionvector=[2 8 13]
        # only look at v2 pitches from recent experiments
        newdata = newdata[(newdata.pitchoftarg == 1) | (newdata.pitchoftarg == 2) | (newdata.pitchoftarg == 3) | (
                newdata.pitchoftarg == 5) | (newdata.pitchoftarg == 8) | (newdata.pitchoftarg == 13)]

        newdata = newdata[(newdata.correctionTrial == 0)]  # | (allData.response == 7)
        newdata = newdata[(newdata.currAtten == 0)]  # | (allData.response == 7)
        if includefaandmiss is True:
            newdata = newdata[(newdata.response == 0) | (newdata.response == 1) | (newdata.response == 7)]
        else:
            newdata = newdata[(newdata.response == 0) | (newdata.response == 1)]
            newdata = newdata[(newdata.catchTrial == 0)]
        if includefaandmiss is False:
            newdata = newdata[(newdata.correctresp == 1)]
        bigdata = bigdata.append(newdata)
    return bigdata


# editing to extract different vars from df
def run_mixed_effects_analysis(ferrets):
    df = get_df_behav(ferrets=ferrets, includefaandmiss=False, startdate='04-01-2020', finishdate='01-10-2022')

    dfuse = df[["pitchoftarg", "pitchofprecur", "talker", "side", "precur_and_targ_same",
                "timeToTarget", "DaysSinceStart", "AM",
                "realRelReleaseTimes", "ferret", "stepval", "pitchofprecur"]]
    X = df[["pitchoftarg", "pitchofprecur", "talker", "side",
            "timeToTarget", "DaysSinceStart", "AM"]].to_numpy()

    modelreg = Lmer(
        "realRelReleaseTimes ~ talker*(pitchoftarg)+ talker*(stepval)+ side + timeToTarget + DaysSinceStart + AM  + (1|ferret)",
        data=dfuse, family='gamma')

    print(modelreg.fit(factors={"side": ["0", "1"], "stepval": ["0.0", "1.0", "2.0"], "AM": ["0", "1"],
                                "pitchoftarg": ['1', '2', '3', '5', '13'], "talker": ["0.0", "1.0"], }, ordered=True,
                       REML=False,
                       old_optimizer=False))

    # looking at whether the response is correct or not
    dfcat = get_df_behav(ferrets=ferrets, includefaandmiss=True, startdate='04-01-2020', finishdate='01-10-2022')

    dfcat_use = dfcat[["pitchoftarg", "pitchofprecur", "talker", "side", "precur_and_targ_same",
                       "timeToTarget", "DaysSinceStart", "AM",
                       "correctresp", "ferret", "stepval", "pitchofprecur"]]

    modelregcat = Lmer(
        "correctresp ~ talker*pitchoftarg +  side  + talker * stepval + stepval+timeToTarget + DaysSinceStart + AM + (1|ferret)",
        data=dfcat_use, family='binomial')

    print(modelregcat.fit(factors={"side": ["0", "1"], "stepval": ["0.0", "1.0", "2.0"], "AM": ["0", "1"],
                                   "pitchoftarg": ['1', '2', '3', '5', '13'], "talker": ["0.0", "1.0"]}, REML=False,
                          old_optimizer=True))

    modelregcat_reduc = Lmer(
        "correctresp ~ talker*pitchoftarg  +  side + timeToTarget +talker*stepval+(1|ferret)",
        data=dfcat_use, family='binomial')

    print(modelregcat_reduc.fit(factors={"side": ["0", "1"],
                                         "pitchoftarg": ['1', '2', '3', '5', '13'], "talker": ["0.0", "1.0"],
                                         "stepval": ["0.0", "1.0", "2.0"]},
                                REML=False,
                                old_optimizer=True))

    modelreg_reduc = Lmer(
        "realRelReleaseTimes ~ talker*(pitchoftarg)+side + talker*stepval+timeToTarget  + (1|ferret)",
        data=dfuse, family='gamma')

    print(modelreg_reduc.fit(factors={"side": ["0", "1"],
                                      "pitchoftarg": ['1', '2', '3', '5', '13'], "talker": ["0.0", "1.0"],
                                      "stepval": ["0.0", "1.0", "2.0"]},
                             ordered=True, REML=False,
                             old_optimizer=False))

    fig, ax = plt.subplots()

    ax = modelregcat.plot_summary()
    plt.title('Model Summary of Coefficients for P(Correct Responses)')
    labels = [item.get_text() for item in ax.get_yticklabels()]

    plt.show()
    fig, ax = plt.subplots()

    ax = modelreg.plot_summary()
    plt.title('Model Summary of Coefficients for Relative Release Times for Correct Responses')
    ax.set_yticklabels(labels)

    plt.show()
    # 1 is 191, 2 is 124, 3 is 144hz female, 5 is 251, 8 is 144hz male, 13 is109hz male
    # pitchof targ 1 is 124hz male, pitchoftarg4 is 109Hz Male

    fig, ax = plt.subplots()

    ax = modelregcat_reduc.plot_summary()
    plt.title('Model Summary of Coefficients for P(Correct Responses)')
    labels = [item.get_text() for item in ax.get_yticklabels()]
    labels[0] = 'Intercept'
    labels[1] = 'male talker vs ref. female talker'
    labels[2] = 'targ - 124 Hz vs ref. 191 Hz'
    labels[3] = 'targ - 144 Hz vs ref. 191 Hz'
    labels[4] = 'targ - 251 Hz vs ref. 191 Hz'
    labels[5] = 'side - right vs ref. left'
    labels[6] = 'time to target'
    labels[7] = 'pos. step from precursor to target'
    labels[8] = 'neg. step from precursor to target'
    labels[9] = 'targ pitch ~ step val'

    ax.set_yticklabels(labels)
    plt.gca().get_yticklabels()[0].set_color("blue")
    plt.gca().get_yticklabels()[1].set_color("blue")
    plt.gca().get_yticklabels()[2].set_color("blue")
    plt.gca().get_yticklabels()[3].set_color("blue")
    plt.gca().get_yticklabels()[4].set_color("blue")
    plt.gca().get_yticklabels()[5].set_color("blue")
    plt.gca().get_yticklabels()[8].set_color("blue")
    plt.show()

    fig, ax = plt.subplots()

    ax = modelreg_reduc.plot_summary()

    plt.title('Model Summary of Coefficients for Correct Release Times')
    labels = [item.get_text() for item in ax.get_yticklabels()]
    labels[0] = 'Intercept'
    labels[1] = 'male talker vs ref. female talker'
    labels[2] = 'targ - 124 Hz vs ref. 191 Hz'
    labels[3] = 'targ - 144 Hz vs ref. 191 Hz'
    labels[4] = 'targ - 251 Hz vs ref. 191 Hz'
    labels[5] = 'side - right vs ref. left'
    labels[6] = 'pos. step in F0 \n b/t precursor and talker'
    labels[7] = 'neg. step in F0 \n b/t precursor and talker'
    labels[8] = 'time to target'
    labels[9] = 'talker corr. with stepval'

    ax.set_yticklabels(labels, fontsize=10)
    plt.gca().get_yticklabels()[0].set_color("blue")
    plt.gca().get_yticklabels()[2].set_color("blue")
    plt.gca().get_yticklabels()[3].set_color("blue")
    plt.gca().get_yticklabels()[4].set_color("blue")
    plt.gca().get_yticklabels()[5].set_color("blue")
    plt.gca().get_yticklabels()[8].set_color("blue")

    plt.show()
    explainedvar = performance.r2_nakagawa(modelregcat_reduc.model_obj, by_group=False, tolerance=1e-05)
    explainedvar_nagelkerke = performance.r2(modelregcat_reduc.model_obj)
    explainvarreleasetime = performance.r2_nakagawa(modelreg_reduc.model_obj, by_group=False, tolerance=1e-05)
    print(explainedvar)
    # side of audio likely adds behavioural noise to the data
    print(explainedvar_nagelkerke)
    ##the marginal R2 encompassing variance explained by only the fixed effects, and the conditional R2 comprising variance explained by both
    # fixed and random effects i.e. the variance explained by the whole model
    print(explainvarreleasetime)
    # TODO: need to make new data frame that is converted to R which only includes individual ferret names, then plot the individual ferrets' responses

    #    data_from_ferret = dfuse.loc[[dfuse['pitchoftarg'] == 1 | dfuse['pitchoftarg'] == 2]]
    data_from_ferret = dfuse[(dfuse['pitchoftarg'] == 1) | (dfuse['pitchoftarg'] == 13)]
    data_from_ferret.isnull().values.any()
    predictedrelease = rstats.predict(modelreg_reduc.model_obj, type='response')
    # with localconverter(ro.default_converter + pandas2ri.converter):
    #     r_from_pd_df = ro.conversion.py2rpy(data_from_ferret)
    # predictedrelease_cruella=rstats.predict(modelreg_reduc.model_obj,  newdata=r_from_pd_df)
    predictedcorrectresp = rstats.predict(modelregcat_reduc.model_obj, type='response')
    # write all applicable dataframes to csv files
    p = 'D:/dfformixedmodels/'
    os.path.normpath(p)
    from pathlib import Path
    filepath = Path('D:/dfformixedmodels/dfuse.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    dfuse.to_csv(filepath)

    filepath = Path('D:/dfformixedmodels/dfcat.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    dfcat.to_csv(filepath)

    filepath = Path('D:/dfformixedmodels/df.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath)

    filepath = Path('D:/dfformixedmodels/dfcat_use.csv')
    dfcat_use.to_csv(filepath)

    # dfuse.to_csv('dfuse.csv', sep=',', path_or_buf=os.PathLike['D:/dfformixedmodels/'])
    # dfcat_use.to_csv('dfcat_use.csv', path_or_buf=os.path.normpath(p))
    # df.to_csv('df.csv', path_or_buf=os.path.normpath(p))
    # dfcat.to_csv('dfcat.csv', path_or_buf=os.path.normpath(p))

    return modelreg_reduc, modelregcat_reduc, modelregcat, modelreg, predictedrelease, dfuse, dfcat_use, predictedcorrectresp, explainedvar, explainvarreleasetime


def plotpredictedversusactual(predictedrelease, dfuse):
    fig, ax = plt.subplots()
    ax.scatter(dfuse['realRelReleaseTimes'], predictedrelease, alpha=0.5)
    ax.set_xlabel('Actual Release Time')
    ax.set_ylabel('Predicted Release Time (s)')
    ax.set_title('Predicted vs. Actual Release Time (s)')
    ax.plot([0, 1], [0, 1], transform=ax.transAxes)
    plt.show()
    fig, ax = plt.subplots()
    ax.scatter(dfuse['realRelReleaseTimes'], dfuse['realRelReleaseTimes'] - predictedrelease, alpha=0.5)
    ax.set_xlabel('Actual Release Time (s)')
    ax.set_ylabel('Actual - Predicted Release Time (s)')
    ax.set_title('Actual - Predicted Release Time (s)')
    ax.plot([0, 1], [0, 0], transform=ax.transAxes)
    plt.show()


def plotpredictedversusactualcorrectresponse(predictedcorrectresp, dfcat_use):
    fig, ax = plt.subplots()
    ax.scatter(dfcat_use['correctresp'], predictedcorrectresp, alpha=0.5)
    ax.set_xlabel('Actual Correct Response')
    ax.set_ylabel('Predicted Correct Response')
    ax.set_title('Predicted vs. Actual Correct Response')
    ax.plot([0, 1], [0, 0], transform=ax.transAxes)
    plt.show()
    # np round rounds down to the nearest integer
    cm = sklearn.metrics.confusion_matrix(dfcat_use['correctresp'], np.round(predictedcorrectresp))
    sklearn.metrics.ConfusionMatrixDisplay(cm, display_labels=['Incorrect', 'Correct']).plot()
    accuracy = sklearn.metrics.accuracy_score(dfcat_use['correctresp'], np.round(predictedcorrectresp))
    plt.show()
    print(accuracy)


if __name__ == '__main__':
    ferrets = ['F1702_Zola', 'F1815_Cruella', 'F1803_Tina', 'F2002_Macaroni']
    modelreg_reduc, modelregcat_reduc, modelregcat, modelreg, predictedrelease, df_use, dfcat_use, predictedcorrectresp, explainedvar, explainvarreleasetime = run_mixed_effects_analysis(
        ferrets)
    plotpredictedversusactual(predictedrelease, df_use)
    plotpredictedversusactualcorrectresponse(predictedcorrectresp, dfcat_use)
