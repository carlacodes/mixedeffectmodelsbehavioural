import click
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

from scipy.stats import sem
import os
import numpy as np
from instruments.helpers.extract_helpers import extractAllFerretData
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from pysr3.lme.models import L1LmeModelSR3
from pysr3.lme.problems import LMEProblem, LMEStratifiedShuffleSplit
import numpy as np
from pysr3.linear.models import LinearL1ModelSR3
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import RandomizedSearchCV
from sklearn.utils.fixes import loguniform
import statistics as stats


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

    #    if ferrets is not None:
    #        ferrets = [ferrets]
    #    else:
    #        ferrets = [ferret for ferret in next(os.walk(db_path))[1] if ferret.startswith('F')]

    dataSet = BehaviourDataSet(filepath=path,
                               startDate=startdate,
                               finishDate=finishdate,
                               ferrets=ferrets,
                               outDir=output)
    allData, ferrets = extractAllFerretData(ferrets, path, startDate=startdate,
                                            finishDate=finishdate)
    fs = 24414.062500
    if includefaandmiss is True:
        newdata = allData[(allData.response == 0) | (allData.response == 1) | (allData.response == 7)]
    else:
        newdata = allData[(allData.response == 0) | (allData.response == 1)]
        newdata = newdata[(newdata.catchTrial == 0)]

    newdata = newdata[(newdata.correctionTrial == 0)]  # | (allData.response == 7)
    newdata = newdata[(newdata.currAtten == 0)]  # | (allData.response == 7)

    # newdata = allData['absentTime'][0]
    newdata['targTimes'] = newdata['timeToTarget'] / fs

    newdata['centreRelease'] = newdata['lickRelease'] - newdata['startTrialLick']
    newdata['relReleaseTimes'] = newdata['centreRelease'] - newdata['targTimes']
    newdata['realRelReleaseTimes'] = newdata['relReleaseTimes'] - newdata['absentTime']
    try:
        pitchshiftmat = newdata['PitchShiftMat']
    except:
        pitchshiftmat = newdata['talker']  # if this is inter trial roving then talker is the pitch shift
    precursorlist = newdata['distractors']
    talkerlist = newdata['talker']
    chosenresponse = newdata['response']
    pitchoftarg = np.empty(len(pitchshiftmat))
    pitchofprecur = np.empty(len(pitchshiftmat))
    gradinpitch = np.empty(len(pitchshiftmat))
    gradinpitchprecur = np.empty(len(pitchshiftmat))
    timetotarglist = np.empty(len(pitchshiftmat))
    precur_and_targ_same = np.empty(len(pitchshiftmat))
    correctresp = np.empty(shape=(0, 0))
    droplist = np.empty(shape=(0, 0))

    for i in range(0, len(talkerlist)):
        chosenresponseindex = chosenresponse.values[i]
        chosentrial = pitchshiftmat.values[i]

        chosendisttrial = precursorlist.values[i]
        chosentalker = talkerlist.values[i]

        if chosentalker == 1:
            origF0 = 191
        else:
            origF0 = 124

        targpos = np.where(chosendisttrial == 1)
        if chosenresponseindex == 0 or chosenresponseindex == 1:
            correctresp = np.append(correctresp, 1)
        else:
            correctresp = np.append(correctresp, 0)
        try:
            pitchoftarg[i] = chosentrial[targpos[0] - 1]
            pitchofprecur[i] = chosentrial[targpos[0] - 2]
            if pitchoftarg[i] == pitchofprecur[i]:
                precur_and_targ_same[i] = 1
            else:
                precur_and_targ_same[i] = 0


        except:
            indexdrop = newdata.iloc[i].name
            newdata.drop(indexdrop, axis=0, inplace=True)
            droplist = np.append(droplist, i)
            continue

    pitchoftarg = pitchoftarg[~np.isnan(pitchoftarg)]
    pitchoftarg = pitchoftarg.astype(int)
    pitchofprecur = pitchofprecur[~np.isnan(pitchofprecur)]
    gradinpitch = gradinpitch[~np.isnan(gradinpitch)]
    # gradinpitchprecur = gradinpitchprecur[~np.isnan(gradinpitchprecur)]
    correctresp = correctresp[~np.isnan(correctresp)]
    #
    # pitchoftarg2 = np.empty(shape=(0, 0))
    # gradinpitch2 = np.empty(shape=(0, 0))
    #
    # pitchofprecur2 = np.empty(shape=(0, 0))
    # gradinpitchprecur2 = np.empty(shape=(0, 0))

    # for i in range(0, len(pitchofprecur)):
    #     if pitchofprecur[i] > 1:
    #         pitchofprecur2 = np.append(pitchofprecur2, pitchofprecur[i])
    #         gradinpitchprecur2 = np.append(gradinpitchprecur2, gradinpitchprecur[i])
    #
    # for i in range(0, len(pitchoftarg)):
    #     if pitchoftarg[i] > 1:
    #         pitchoftarg2 = np.append(pitchoftarg2, pitchoftarg[i])
    #         gradinpitch2 = np.append(gradinpitch2, gradinpitch[i])

    # pitchoftarg2 = pitchoftarg2 / np.linalg.norm(
    #     pitchoftarg2)  # np.array(scaler.fit_transform(pitchoftarg2.reshape(-1, 1)))
    # pitchofprecur2 = pitchofprecur2 / np.linalg.norm(
    #     pitchofprecur2)  # np.array(scaler.fit_transform(pitchofprecur2.reshape(-1, 1)))
    # gradinpitch2 = gradinpitch2 / np.linalg.norm(
    #     gradinpitch2)  # np.array(scaler.fit_transform(gradinpitch2.reshape(-1, 1)))
    # gradinpitchprecur2 = gradinpitchprecur2 / np.linalg.norm(
    #     gradinpitchprecur2)  # np.array(scaler.fit_transform(gradinpitchprecur2.reshape(-1, 1)))
    # pitchofprecur2 = np.array(scaler.fit_transform(pitchofprecur2.reshape(-1, 1)))
    # gradinpitch2 =  np.array(scaler.fit_transform(pitchofprecur2.reshape(-1, 1)))
    # gradinpitchprecur2 = np.array(scaler.fit_transform(gradinpitchprecur2.reshape(-1, 1)))

    # df_normalized = pd.DataFrame(x_scaled)

    newdata['pitchoftarg'] = pitchoftarg.tolist()
    pitchofprecur = np.delete(pitchofprecur, droplist)
    newdata['pitchofprecur'] = pitchofprecur.tolist()

    droplist = [int(x) for x in droplist]
    correctresp = np.delete(correctresp, droplist)
    correctresp = correctresp.astype(int)
    newdata['correctresp'] = correctresp.tolist()
    precur_and_targ_same = precur_and_targ_same.astype(int)
    newdata['precur_and_targ_same'] = precur_and_targ_same.tolist()
    newdata['timeToTarget'] = newdata['timeToTarget'] / 24414.0625
    newdata['AM'] = newdata['AM'].astype(int)
    newdata['talker'] = (newdata['talker']).astype(float)
    return newdata

    # ferretFigs = reactionTimeAnalysis(ferrData)
    # dataSet._save(figs=ferretFigs, file_name='reaction_times_{}_{}_{}.pdf'.format(ferret, startdate, finishdate))


# editing to extract different vars from df
# cli.add_command(cli_reaction_time)

if __name__ == '__main__':
    ferrets = ['F1702_Zola', 'F1815_Cruella', 'F1803_Tina', 'F2002_Macaroni']
    # for i, currFerr in enumerate(ferrets):
    #     print(i, currFerr)
    df = get_df_behav(ferrets=ferrets, includefaandmiss=False, startdate='04-01-2020', finishdate='01-10-2022')

    dfuse = df[["pitchoftarg", "pitchofprecur", "talker", "side", "precur_and_targ_same",
                "timeToTarget", "DaysSinceStart", "AM",
                "realRelReleaseTimes", "ferret"]]
    endog2 = df['realRelReleaseTimes'].to_numpy()

    # TODO: CLEAN CODE
    import numpy as np

    X = df[["pitchoftarg", "pitchofprecur", "talker", "side",
            "timeToTarget", "DaysSinceStart", "AM"]].to_numpy()

    y = endog2
    modelreg = Lmer(
        "realRelReleaseTimes ~ pitchoftarg + talker +  side  + precur_and_targ_same + timeToTarget + DaysSinceStart + AM + (1|ferret)",
        data=dfuse, family='gaussian')

    print(modelreg.fit(factors={"side": ["0", "1"], "precur_and_targ_same": ['1', '0'], "AM": ["0", "1"],
                                "pitchoftarg": ['0', '11', '5', '1', '13', '2', '6', '9', '12', '4', '8', '3',
                                                '14', '10', '7'], "talker": ["2.0", "1.0"], }, REML=False,
                       old_optimizer=True))

    dfcat = get_df_behav(ferrets=ferrets, includefaandmiss=True, startdate='04-01-2020', finishdate='01-10-2022')
    dfcat_use = df[["pitchoftarg", "pitchofprecur", "talker", "side", "precur_and_targ_same",
                    "timeToTarget", "DaysSinceStart", "AM",
                    "correctresp", "ferret"]]

    modelregcat = Lmer(
        "correcpresp ~ pitchoftarg + talker +  side  + precur_and_targ_same + timeToTarget + DaysSinceStart + AM + (1|ferret)",
        data=dfuse, family='binomial')

    print(modelregcat.fit(factors={"side": ["0", "1"], "precur_and_targ_same": ['1', '0'], "AM": ["0", "1"],
                                   "pitchoftarg": ['0', '11', '5', '1', '13', '2', '6', '9', '12', '4', '8', '3',
                                                   '14', '10', '7'], "talker": ["2.0", "1.0"], }, REML=False,
                          old_optimizer=True))
