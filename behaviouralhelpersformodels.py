
from instruments.config import behaviouralDataPath, behaviourOutput
from sklearn.preprocessing import MinMaxScaler
from instruments.helpers.extract_helpers import extractAllFerretData
import pandas as pd
import numpy as np
import pandas as pd


class behaviouralhelperscg:

    def get_false_alarm_behavdata(path=None,
                     output=None,
                     ferrets=None,
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

            precursorlist = newdata['distractors']
            catchtriallist = newdata['catchTrial']
            chosenresponse = newdata['response']
            realrelreleasetimelist = newdata['realRelReleaseTimes']
            pitchoftarg = np.empty(len(pitchshiftmat))
            pitchofprecur = np.empty(len(pitchshiftmat))
            stepval = np.empty(len(pitchshiftmat))
            distractor_or_fa = np.empty(len(pitchshiftmat))
            gradinpitch = np.empty(len(pitchshiftmat))
            gradinpitchprecur = np.empty(len(pitchshiftmat))
            timetotarglist = np.empty(len(pitchshiftmat))

            precur_and_targ_same = np.empty(len(pitchshiftmat))
            intra_trial_roving = np.empty(len(pitchshiftmat))
            talkerlist2 = np.empty(len(pitchshiftmat))

            falsealarm = np.empty(shape=(0, 0))
            correctresp = np.empty(shape=(0, 0))
            pastcorrectresp = np.empty(shape=(0, 0))
            pastcatchtrial = np.empty(shape=(0, 0))
            droplist = np.empty(shape=(0, 0))
            droplistnew = np.empty(shape=(0, 0))

            for i in range(1, len(newdata['realRelReleaseTimes'].values)):
                chosenresponseindex = chosenresponse.values[i]
                pastcatchtrialindex = catchtriallist.values[i - 1]

                realrelreleasetime = realrelreleasetimelist.values[i]
                pastrealrelreleasetime = realrelreleasetimelist.values[i - 1]
                pastresponseindex = chosenresponse.values[(i - 1)]

                chosentrial = pitchshiftmat.values[i]
                is_all_zero = np.all((chosentrial == 0))
                if isinstance(chosentrial, float) or is_all_zero:
                    chosentrial = talkermat.values[i].astype(int)
                    intra_trial_roving[i] = 0
                else:
                    intra_trial_roving[i] = 1

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

                if ((
                            chosenresponseindex == 0 or chosenresponseindex == 1) and realrelreleasetime >= 0) or chosenresponseindex == 3 or chosenresponseindex==7:
                    falsealarm = np.append(falsealarm, 0)
                else:
                    falsealarm = np.append(falsealarm, 1)
                if ((
                            chosenresponseindex == 0 or chosenresponseindex == 1) and realrelreleasetime >= 0) or chosenresponseindex == 3:
                    correctresp = np.append(correctresp, 1)
                else:
                    correctresp = np.append(correctresp, 0)

                if ((
                            pastresponseindex == 0 or pastresponseindex == 1) and pastrealrelreleasetime >= 0) or pastresponseindex == 3:
                    pastcorrectresp = np.append(pastcorrectresp, 1)
                else:
                    pastcorrectresp = np.append(pastcorrectresp, 0)

                if pastcatchtrialindex == 1:
                    pastcatchtrial = np.append(pastcatchtrial, 1)
                else:
                    pastcatchtrial = np.append(pastcatchtrial, 0)
                try:
                    targpos = np.where(chosendisttrial == 1)
                    distractor_or_fa[i] = chosendisttrial[targpos[0] - 1]

                    if chosentrial[targpos[0]] == 8.0:
                        pitchoftarg[i] == 3.0
                    else:
                        pitchoftarg[i] = chosentrial[targpos[0]]

                    if chosentrial[targpos[0] - 1] == 8.0:
                        pitchofprecur[i] == 3
                    else:
                        pitchofprecur[i] = chosentrial[targpos[0] - 1]
                        # 1 is 191, 2 is 124, 3 is 144hz female, 5 is 251, 8 is 144hz male, 13 is109hz male
                        # pitchof targ 1 is 124hz male, pitchoftarg4 is 109Hz Male

                    if chosentrial[targpos[0] - 1] == 3.0:
                        stepval[i] = 1.0
                    elif chosentrial[targpos[0] - 1] == 8.0:
                        stepval[i] = -1.0
                    elif chosentrial[targpos[0] - 1] == 13.0:
                        stepval[i] = 1.0
                    elif chosentrial[targpos[0] - 1] == 5.0:
                        stepval[i] = -1.0
                    else:
                        stepval[i] = 0.0

                    if pitchofprecur[i] == 1.0:
                        pitchofprecur[i] = 4.0

                    if pitchofprecur[i] == 13.0:
                        pitchofprecur[i] = 1.0

                    if pitchoftarg[i] == 1.0:
                        pitchoftarg[i] = 4.0

                    if pitchoftarg[i] == 13.0:
                        pitchoftarg[i] = 1.0



                except:
                    indexdrop = newdata.iloc[i].name
                    #droplist = np.append(droplist, i - 1)
                    #arrays START AT 0, but the index starts at 1, so the index is 1 less than the array
                    #droplistnew = np.append(droplistnew, indexdrop)
                    pitchoftarg[i] = np.nan
                    if isinstance(chosentrial, int):
                        pitchofprecur[i] = chosentrial
                    else:
                        pitchofprecur[i] =chosentrial[-1]
                    if pitchofprecur[i] == 1.0:
                        pitchofprecur[i] = 4.0

                    if pitchofprecur[i] == 13.0:
                        pitchofprecur[i] = 1.0

                    if pitchoftarg[i] == 1.0:
                        pitchoftarg[i] = 4.0

                    if pitchoftarg[i] == 13.0:
                        pitchoftarg[i] = 1.0
                    distractor_or_fa[i] = chosendisttrial[-1]
                    continue
            newdata.drop(index=newdata.index[0],
                         axis=0,
                         inplace=True)
            #newdata.drop(droplistnew, axis=0, inplace=True)
            droplist = [int(x) for x in droplist]  # drop corrupted metdata trials

            pitchoftarg = pitchoftarg.astype(int)
            pitchofprecur = pitchofprecur.astype(int)
            falsealarm = falsealarm[~np.isnan(falsealarm)]
            correctresp = correctresp[~np.isnan(correctresp)]

            pitchoftarg = np.delete(pitchoftarg, 0)
            talkerlist2 = np.delete(talkerlist2, 0)
            distractor_or_fa = np.delete(distractor_or_fa, 0)
            stepval = np.delete(stepval, 0)
            pitchofprecur = np.delete(pitchofprecur, 0)
            intra_trial_roving = np.delete(intra_trial_roving, 0)


            # pitchoftarg = np.delete(pitchoftarg, droplist)
            # talkerlist2 = np.delete(talkerlist2, droplist)
            # stepval = np.delete(stepval, droplist)

            newdata['pitchoftarg'] = pitchoftarg.tolist()

            # pitchofprecur = np.delete(pitchofprecur, droplist)
            newdata['pitchofprecur'] = pitchofprecur.tolist()

            # falsealarm = np.delete(falsealarm, droplist)
            # pastcorrectresp = np.delete(pastcorrectresp, droplist)
            # pastcatchtrial = np.delete(pastcatchtrial, droplist)

            falsealarm = falsealarm.astype(int)
            pastcatchtrial = pastcatchtrial.astype(int)
            pastcorrectresp = pastcorrectresp.astype(int)


            newdata['falsealarm'] = falsealarm.tolist()
            newdata['intra_trial_roving'] = intra_trial_roving.tolist()
            newdata['correctresp'] = correctresp.tolist()
            newdata['distractor_or_fa'] = distractor_or_fa.tolist()
            newdata['pastcorrectresp'] = pastcorrectresp.tolist()
            newdata['talker'] = talkerlist2.tolist()
            newdata['pastcatchtrial'] = pastcatchtrial.tolist()
            newdata['stepval'] = stepval.tolist()
            newdata['timeToTarget'] = newdata['timeToTarget'] / 24414.0625
            newdata['AM'] = newdata['AM'].astype(int)
            newdata['talker'] = newdata['talker'] - 1
            newdata = newdata[newdata['distractor_or_fa'].values<=57]

            cosinesimfemale = np.load('D:/Stimuli/cosinesimvectorfemale.npy')
            cosinesimmale = np.load('D:/Stimuli/cosinesimvectormale.npy')

            distinds = newdata['distractor_or_fa'].values
            distinds = distinds-1;
            correspondcosinelist = []
            for i in range(len(distinds)):
                if newdata['talker'].values[i] == 0:
                    correspondcosinelist.append(cosinesimfemale[int(distinds[i])])
                else:
                    correspondcosinelist.append(cosinesimmale[int(distinds[i])])
            newdata['cosinesim'] = correspondcosinelist

            newdata = newdata[(newdata.pitchoftarg == 1) | (newdata.pitchoftarg == 2) | (newdata.pitchoftarg == 3) | (
                    newdata.pitchoftarg == 4) | (newdata.pitchoftarg == 5)]
            newdata = newdata[
                (newdata.pitchofprecur == 1) | (newdata.pitchofprecur == 2) | (newdata.pitchofprecur == 3) | (
                        newdata.pitchofprecur == 4) | (newdata.pitchofprecur == 5)]
            # newdata = newdata[
            #     (newdata.response == 1) | (newdata.response == 0) | (newdata.response == 5) | (
            #             newdata.pitchofprecur == 4) | (newdata.pitchofprecur == 5)]

            newdata = newdata[(newdata.correctionTrial == 0)]  # | (allData.response == 7)
            newdata = newdata[(newdata.currAtten == 0)]  # | (allData.response == 7)
            newdata = newdata[(newdata.catchTrial == 0)]  # | (allData.response == 7)


            bigdata = bigdata.append(newdata)
        return bigdata
    def get_reactiontime_data(path=None,
                     output=None,
                     ferrets=None,
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

            newdata = allData[allData['ferret'] == ferret]
            newdata = newdata[
                (newdata.response == 1) | (newdata.response == 0) | (newdata.response == 5) ] #remove all misses
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
            precursorlist = newdata['distractors']
            catchtriallist = newdata['catchTrial']
            chosenresponse = newdata['response']
            realrelreleasetimelist = newdata['realRelReleaseTimes']
            pitchoftarg = np.empty(len(pitchshiftmat))
            pitchofprecur = np.empty(len(pitchshiftmat))
            stepval = np.empty(len(pitchshiftmat))
            distractor_or_fa = np.empty(len(pitchshiftmat))
            intra_trial_roving = np.empty(len(pitchshiftmat))
            control_trial = np.empty(len(pitchshiftmat))

            talkerlist2 = np.empty(len(pitchshiftmat))
            falsealarm = np.empty(shape=(0, 0))
            correctresp = np.empty(shape=(0, 0))
            pastcorrectresp = np.empty(shape=(0, 0))
            pastcatchtrial = np.empty(shape=(0, 0))



            for i in range(1, len(newdata['realRelReleaseTimes'].values)):
                chosenresponseindex = chosenresponse.values[i]
                pastcatchtrialindex = catchtriallist.values[i - 1]

                realrelreleasetime = realrelreleasetimelist.values[i]
                pastrealrelreleasetime = realrelreleasetimelist.values[i - 1]
                pastresponseindex = chosenresponse.values[(i - 1)]
                current_distractors = distractors.values[i]
                current_dDurs = newdata['dDurs'].values[i]/24414.062500
                current_releasetime = newdata['centreRelease'].values[i]
                curr_dur_list = []
                current_dist_list=[]
                current_dur=[]
                for i in range(0, len(current_distractors)):
                  current_dur = np.sum(current_dDurs[0:(i + 1)])
                  print(current_dur)
                  print(i)

                  if current_dur <= current_releasetime:
                    print('current dur', current_dur)
                    curr_dur_list.append(current_dur)
                    current_dist_list.append(current_distractors[i])
                  else:
                      break

                print('current dist list', current_dist_list)
                try:
                    distractor_or_fa[i] = current_dist_list[-1]
                except:
                    distractor_or_fa[i] = current_distractors[0]





                chosentrial = pitchshiftmat.values[i]
                is_all_zero = np.all((chosentrial == 0))


                if is_all_zero:
                    control_trial[i]  = 1
                else:
                    control_trial[i]  = 0

                if isinstance(chosentrial, float) or is_all_zero:
                    chosentrial = talkermat.values[i].astype(int)
                    intra_trial_roving[i] = 0
                else:
                    intra_trial_roving[i] = 1

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

                if ((
                            chosenresponseindex == 0 or chosenresponseindex == 1) and realrelreleasetime >= 0) or chosenresponseindex == 3 or chosenresponseindex==7:
                    falsealarm = np.append(falsealarm, 0)
                else:
                    falsealarm = np.append(falsealarm, 1)
                if ((
                            chosenresponseindex == 0 or chosenresponseindex == 1) and realrelreleasetime >= 0) or chosenresponseindex == 3:
                    correctresp = np.append(correctresp, 1)
                else:
                    correctresp = np.append(correctresp, 0)

                if ((
                            pastresponseindex == 0 or pastresponseindex == 1) and pastrealrelreleasetime >= 0) or pastresponseindex == 3:
                    pastcorrectresp = np.append(pastcorrectresp, 1)
                else:
                    pastcorrectresp = np.append(pastcorrectresp, 0)

                if pastcatchtrialindex == 1:
                    pastcatchtrial = np.append(pastcatchtrial, 1)
                else:
                    pastcatchtrial = np.append(pastcatchtrial, 0)
                try:
                    targpos = np.where(chosendisttrial == 1)

                    if chosentrial[targpos[0]] == 8.0:
                        pitchoftarg[i] == 3.0
                    else:
                        pitchoftarg[i] = chosentrial[targpos[0]]

                    if chosentrial[targpos[0] - 1] == 8.0:
                        pitchofprecur[i] == 3
                    else:
                        pitchofprecur[i] = chosentrial[targpos[0] - 1]
                        # 1 is 191, 2 is 124, 3 is 144hz female, 5 is 251, 8 is 144hz male, 13 is109hz male
                        # pitchof targ 1 is 124hz male, pitchoftarg4 is 109Hz Male

                    if chosentrial[targpos[0] - 1] == 3.0:
                        stepval[i] = 1.0
                    elif chosentrial[targpos[0] - 1] == 8.0:
                        stepval[i] = -1.0
                    elif chosentrial[targpos[0] - 1] == 13.0:
                        stepval[i] = 1.0
                    elif chosentrial[targpos[0] - 1] == 5.0:
                        stepval[i] = -1.0
                    else:
                        stepval[i] = 0.0

                    if pitchofprecur[i] == 1.0:
                        pitchofprecur[i] = 4.0

                    if pitchofprecur[i] == 13.0:
                        pitchofprecur[i] = 1.0

                    if pitchoftarg[i] == 1.0:
                        pitchoftarg[i] = 4.0

                    if pitchoftarg[i] == 13.0:
                        pitchoftarg[i] = 1.0



                except:
                    indexdrop = newdata.iloc[i].name
                    #droplist = np.append(droplist, i - 1)
                    #arrays START AT 0, but the index starts at 1, so the index is 1 less than the array
                    #droplistnew = np.append(droplistnew, indexdrop)
                    pitchoftarg[i] = np.nan
                    if isinstance(chosentrial, int):
                        pitchofprecur[i] = chosentrial
                    else:
                        pitchofprecur[i] =chosentrial[-1]
                    if pitchofprecur[i] == 1.0:
                        pitchofprecur[i] = 4.0

                    if pitchofprecur[i] == 13.0:
                        pitchofprecur[i] = 1.0

                    if pitchoftarg[i] == 1.0:
                        pitchoftarg[i] = 4.0

                    if pitchoftarg[i] == 13.0:
                        pitchoftarg[i] = 1.0
                    continue
            newdata.drop(index=newdata.index[0],
                         axis=0,
                         inplace=True)

            pitchoftarg = pitchoftarg.astype(int)
            pitchofprecur = pitchofprecur.astype(int)
            falsealarm = falsealarm[~np.isnan(falsealarm)]
            correctresp = correctresp[~np.isnan(correctresp)]

            pitchoftarg = np.delete(pitchoftarg, 0)
            talkerlist2 = np.delete(talkerlist2, 0)
            distractor_or_fa = np.delete(distractor_or_fa, 0)
            stepval = np.delete(stepval, 0)
            pitchofprecur = np.delete(pitchofprecur, 0)
            intra_trial_roving = np.delete(intra_trial_roving, 0)


            newdata['pitchoftarg'] = pitchoftarg.tolist()

            newdata['pitchofprecur'] = pitchofprecur.tolist()

            falsealarm = falsealarm.astype(int)
            pastcatchtrial = pastcatchtrial.astype(int)
            pastcorrectresp = pastcorrectresp.astype(int)


            newdata['falsealarm'] = falsealarm.tolist()
            newdata['intra_trial_roving'] = intra_trial_roving.tolist()
            newdata['correctresp'] = correctresp.tolist()
            newdata['distractor_or_fa'] = distractor_or_fa.tolist()
            newdata['pastcorrectresp'] = pastcorrectresp.tolist()
            newdata['talker'] = talkerlist2.tolist()
            newdata['pastcatchtrial'] = pastcatchtrial.tolist()
            newdata['stepval'] = stepval.tolist()
            newdata['timeToTarget'] = newdata['timeToTarget'] / 24414.0625
            newdata['AM'] = newdata['AM'].astype(int)
            newdata['talker'] = newdata['talker'] - 1
            newdata = newdata[newdata['distractor_or_fa'].values <= 57]

            cosinesimfemale = np.load('D:/Stimuli/cosinesimvectorfemale.npy')
            cosinesimmale = np.load('D:/Stimuli/cosinesimvectormale.npy')

            distinds = newdata['distractor_or_fa'].values
            distinds = distinds-1;
            correspondcosinelist = []
            for i in range(len(distinds)):
                if newdata['talker'].values[i] == 0:
                    correspondcosinelist.append(cosinesimfemale[int(distinds[i])])
                else:
                    correspondcosinelist.append(cosinesimmale[int(distinds[i])])
            newdata['cosinesim'] = correspondcosinelist

            # newdata = newdata[(newdata.pitchoftarg == 1) | (newdata.pitchoftarg == 2) | (newdata.pitchoftarg == 3) | (
            #         newdata.pitchoftarg == 4) | (newdata.pitchoftarg == 5)]
            # newdata = newdata[
            #     (newdata.pitchofprecur == 1) | (newdata.pitchofprecur == 2) | (newdata.pitchofprecur == 3) | (
            #             newdata.pitchofprecur == 4) | (newdata.pitchofprecur == 5)]
            # newdata = newdata[
            #     (newdata.response == 1) | (newdata.response == 0) | (newdata.response == 5) ] #remove all misses

            newdata = newdata[(newdata.correctionTrial == 0)]  # | (allData.response == 7)
            newdata = newdata[(newdata.currAtten == 0)]  # | (allData.response == 7)

            emptydistracotrindexdict_categorical = dict.fromkeys((range(1,56)))
            emptydistracotrindexdict_categorical = {str(k): str(v) for k, v in emptydistracotrindexdict_categorical.items()}

            dataframeversion = pd.DataFrame.from_dict(emptydistracotrindexdict_categorical, orient='index')
            for i in range(0, len(newdata)):
                #now declare function to get the distractor indices that th eanimal fa-ed to or the correct distractor
                if newdata['distractor_or_fa'].values[i] in emptydistracotrindexdict_categorical:
                    print("Exists")
                    exception_key = str(newdata['distractor_or_fa'].values[i])
                    if exception_key != 1:
                        print('nonone distracotr key =', i)
                    new_entry = float('nan')
                    if i == 0:

                        emptydistracotrindexdict_categorical[newdata['distractor_or_fa'].values[i]] = newdata['centreRelease'].values[i]

                        for key, value in emptydistracotrindexdict_categorical.items():
                            if key == exception_key:
                                emptydistracotrindexdict_categorical[key] = value
                            else:
                                emptydistracotrindexdict_categorical[key] = new_entry
                    else:

                        for key, value in emptydistracotrindexdict_categorical.items():
                            if key == exception_key:
                                current = emptydistracotrindexdict_categorical[key]
                                combined = np.concatenate((current, [float(1)]), axis=None)
                                emptydistracotrindexdict_categorical[key] = combined
                            else:
                                current = emptydistracotrindexdict_categorical[key]
                                combined = np.concatenate((current, [float('nan')]), axis=None)
                                emptydistracotrindexdict_categorical[key] = combined

                else:
                    print("Does not exist")

            #convert to dataframe

            dataframeversion = pd.DataFrame.from_dict(emptydistracotrindexdict_categorical)
            newdata = newdata.append(emptydistracotrindexdict_categorical, ignore_index=True)
            bigdata = bigdata.append(newdata)
        return bigdata