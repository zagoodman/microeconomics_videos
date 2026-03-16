#!/usr/bin/env python
# coding: utf-8

# # View this notebook here:
# https://nbviewer.jupyter.org/github/zagoodman/microeconomics_videos/blob/master/jupyter/assemble_data.ipynb

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Prep" data-toc-modified-id="Prep-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Prep</a></span></li><li><span><a href="#Merge-anonymized-data" data-toc-modified-id="Merge-anonymized-data-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Merge anonymized data</a></span><ul class="toc-item"><li><span><a href="#Demographic-data" data-toc-modified-id="Demographic-data-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Demographic data</a></span><ul class="toc-item"><li><span><a href="#Preceding-term-vars" data-toc-modified-id="Preceding-term-vars-2.1.1"><span class="toc-item-num">2.1.1&nbsp;&nbsp;</span>Preceding term vars</a></span></li><li><span><a href="#Student-level" data-toc-modified-id="Student-level-2.1.2"><span class="toc-item-num">2.1.2&nbsp;&nbsp;</span>Student-level</a></span></li><li><span><a href="#GPA-and-course-units" data-toc-modified-id="GPA-and-course-units-2.1.3"><span class="toc-item-num">2.1.3&nbsp;&nbsp;</span>GPA and course units</a></span><ul class="toc-item"><li><span><a href="#Concurrent-term" data-toc-modified-id="Concurrent-term-2.1.3.1"><span class="toc-item-num">2.1.3.1&nbsp;&nbsp;</span>Concurrent term</a></span></li><li><span><a href="#Following-term" data-toc-modified-id="Following-term-2.1.3.2"><span class="toc-item-num">2.1.3.2&nbsp;&nbsp;</span>Following term</a></span></li></ul></li></ul></li><li><span><a href="#Treatment-and-outcome-data" data-toc-modified-id="Treatment-and-outcome-data-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Treatment and outcome data</a></span><ul class="toc-item"><li><span><a href="#Student-level" data-toc-modified-id="Student-level-2.2.1"><span class="toc-item-num">2.2.1&nbsp;&nbsp;</span>Student level</a></span></li></ul></li></ul></li><li><span><a href="#Videos" data-toc-modified-id="Videos-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Videos</a></span><ul class="toc-item"><li><span><a href="#100A" data-toc-modified-id="100A-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>100A</a></span></li><li><span><a href="#Week-level" data-toc-modified-id="Week-level-3.2"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>Week-level</a></span></li><li><span><a href="#Export" data-toc-modified-id="Export-3.3"><span class="toc-item-num">3.3&nbsp;&nbsp;</span>Export</a></span></li><li><span><a href="#100B" data-toc-modified-id="100B-3.4"><span class="toc-item-num">3.4&nbsp;&nbsp;</span>100B</a></span></li><li><span><a href="#Export" data-toc-modified-id="Export-3.5"><span class="toc-item-num">3.5&nbsp;&nbsp;</span>Export</a></span></li></ul></li></ul></div>

# This file takes anonymized data from the T+LC, cleans them, and returns analysis-ready data frames:
# 1. `id-year_level_data.csv`: treatment and exam score data
# 2. `dem_concurrent.csv`: demographic data and GPA/courseload during the quarter of the experiment
# 3. `dem_nextquarter.csv`: demographic data and GPA/courseload during the quarter following treatment
# 
# All code in this file is in Python 3.

# ## Prep

import pandas as pd
import numpy as np
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
from matplotlib import pyplot as plt


import pandas_flavor as pf

@pf.register_dataframe_accessor('z')
class MyFlavor(object):

    def __init__(self, df):
        self._df = df

    def get_unique_students(self, var1 = "id", var2 = "year"):
        df = self._df
        x = len(df[[var1, var2]].drop_duplicates())
        print("N unique students: {}".format(x))
        return x

    def get_vars(self):
        df = self._df
        cols = [x for x in df if x in tlcvarnames]
        return df[cols].rename(columns = tlcvarnames)

tlcvarnames = {'id': 'id',
               'year': 'year',
               'de id': 'id', 
               'deid': 'id',
               'previous_cum_gpa': 'prev_cumgpa',
               'term_code_econ': 'term',
               'term-econ100a': 'term',
               'term code courses': 'term_courses',
               'term_precoursegpa': 'term_pregpa',
               'term code econ 100a': 'termecon',
               'apct_type_desc': 'apptype',
               'ethnicity_grouped': 'ethnicity',
               'gender': 'gender',
               'term_code_econ': 'term',
               'year_econ': 'year',
               'year - econ 100a': 'year',
               'year - econ100a': 'year',
               'year-econ100a': 'year',
               'year-zack': 'year',
               'measure names': 'measure',
               'measure values': 'values',
               'Class Units - Letter Grade': 'units_letter',
               'Class Units - P/NP': 'units_pnp',
               'Class Units - Withdrawn': 'units_w',
               'GPA - Classes Letter Grade': 'gpa_letter',
               'GPA - Classes Letter Grade - No Econ': 'gpa_letter_sansecon',
               'GPA - Classes Letter Grade - No Econ 100A': 'gpa_letter_sans100a',
               'GPA - Classes Letter Grade - Only Econ - No Econ 100A': 'gpa_econ_sans100a',
               'N Classes - Letter Grade': 'nclass_letter',
               'N Classes - Not Passed': 'nclass_np',
               'N Classes - P/NP': 'nclass_pnp',
               'N Classes - Passed': 'nclass_p',
               'N Classes - Withdrawn': 'nclass_w'
              }


# ## Merge anonymized data

# ### Demographic data

# #### Preceding term vars

# pre 100A (term before) cumulative gpa. Missing for all entering freshmen or first time UCSD students

dfd = pd.read_excel("../data/raw/Econ-Goodman-Su20-Pre Course GPA-FA18.xlsx")
dfd = pd.concat([dfd, pd.read_excel("../data/raw/Econ-Goodman-Su20-Pre Course GPA-FA19.xlsx")], 0)
dfd.columns = [x.lower() for x in dfd.columns]
dfd = dfd.z.get_vars()
dfd.loc[dfd.term == 'FA18', 'year'] = 2018
dfd.loc[dfd.term == 'FA19', 'year'] = 2019
# reorder and drop term
dfd = dfd[['id', 'year', 'term_pregpa', 'prev_cumgpa']]

print(len(dfd))
dfd.z.get_unique_students(var2='id')
display(dfd.isnull().sum())
#dfd.head()


# #### Student-level

# ethnicity, gender, transfer status

df = pd.read_excel("../data/raw/Econ-Goodman-Su20-Student-level.xlsx")
df.rename(str.lower, axis=1, inplace=True)
df = df.z.get_vars()
df['transfer'] = np.array(df.apptype == 'Transfer Student', dtype='int')
df.loc[df.gender == 'Men (Cis & Trans)', 'gender'] = 'm'
df.loc[df.gender == 'Women (Cis & Trans)', 'gender'] = 'f'
df.loc[df.gender == 'Data Unavailable', 'gender'] = 'u'
# drop term and reorder
df = df[['id', 'year', 'ethnicity', 'gender', 'transfer', 'apptype']]

# merge with dfd
dfd = df.merge(dfd, how='outer', on=['id', 'year'])

print(len(dfd))
dfd.z.get_unique_students()
print(dfd.isnull().sum())
#dfd.head()


# #### GPA and course units

df = pd.read_excel("../data/raw/Econ-Goodman-Su20-Student-quarter-level_FA18-WI19.xlsx")
df.columns = [x.lower() for x in df.columns]
df = df.z.get_vars()
df2 = pd.read_excel("../data/raw/Econ-Goodman-Su20-Student-quarter-level_FA19-WI20.xlsx")
df2.columns = [x.lower() for x in df2.columns]
df2 = df2.z.get_vars()

df = pd.concat([df, df2], 0)
print(len(df))
display(pd.crosstab(df.year, df.term))


# ##### Concurrent term

## concurrent data

dfc = df.loc[df.term_courses.isin(["FA18", "FA19"])]
dfc = dfc[['id', 'year', 'measure', 'values']]

# reshape wide
dfc = dfc.pivot_table(index=['id', 'year'], columns='measure', values='values').reset_index()
dfc = dfc.z.get_vars()

# merge with rest of demographic data
dfd = dfd.merge(dfc, how='outer', on=['id', 'year'])

# add zeros where needed
for x in ['units_pnp', 'units_w']:
    dfd.loc[dfd[x].isnull(), x] = 0

# check and explore data
print(len(dfd))
dfd.z.get_unique_students()
print(dfd.dtypes)
print(dfd.isnull().sum())

# export
dfd.to_csv("../data/generated/dem_concurrent.csv", index=False)


# ##### Following term

## following quarter's data

dff = df.loc[df.term_courses.isin(["WI19", "WI20"])]
dff = dff[['id', 'year', 'measure', 'values']]

# reshape wide
dff = dff.pivot_table(index=['id', 'year'], columns='measure', values='values').reset_index()
dff = dff.z.get_vars()

# merge with rest of demographic data
dfd = dfd.iloc[:, 0:8]
dfd = dfd.merge(dff, how='outer', on=['id', 'year'])

# add zeros where needed
for x in ['units_letter', 'units_pnp', 'units_w', \
          'nclass_letter', 'nclass_np', 'nclass_pnp', \
          'nclass_p', 'nclass_w']:
    dfd.loc[dfd[x].isnull(), x] = 0

# check and explore data
print(len(dfd))
dfd.z.get_unique_students()
print(dfd.dtypes)
print(dfd.isnull().sum())

# export
dfd.to_csv("../data/generated/dem_nextquarter.csv", index=False)


# ### Treatment and outcome data

# #### Student level

df = pd.read_excel("../data/raw/DeID_all_pid-year-level_data with description.xlsx")
df.rename(columns={'DeID': 'id'}, inplace=True)
print(len(df))
df.z.get_unique_students()
df = df[['id'] + [x for x in df.columns if x != 'id']]
#df.head()


# I think that's all I need for now...may add more later

# drop the two duplicate entries
print(len(df))
df = df.drop_duplicates()
print(len(df))
df.z.get_unique_students()

# export
df.to_csv("../data/generated/id-year_level_data.csv", index=False)


# ## Videos

# ### 100A

dfv = pd.read_csv('../data/raw/DeID_video-level_data.csv')
dfv = dfv.loc[dfv.videoid.notnull()]
dfv.loc[dfv.syllabus_week.isnull(), 'syllabus_week'] = -1

# int columns
for v in dfv.columns[7:-1]:
    dfv[v] = dfv[v].apply(lambda x: int(x))

# date columns
dfv['lastview'] = pd.to_datetime(dfv['last.view'])
dfv['firstview'] = pd.to_datetime(dfv['first.view'])

# unnecessary cols
dfv.drop(['first.view', 'last.view', 'videocode', 'length_mins'], 1, inplace=True)

# get treatment status
df = pd.read_csv("../data/generated/id-year_level_data.csv")
df['arm'] = df.toberandomized + df.treated
df = df[['id', 'year', 'arm', 'finalscore']]
# display(df.head())

# rename 'DeID' to 'id' in dfv, then merge treatment status
dfv.rename(columns={'DeID': 'id'}, inplace=True)
dfv = dfv.merge(df, on=['id', 'year'], how='left')
# dfv.head()

print(dfv.isnull().sum())
dfv.head(2)


# Explore

dftmp = dfv[['syllabus_week', 'incentivized', 'videoid']].drop_duplicates()
print('This many relevant videos: {}'.format(dftmp.syllabus_week.notnull().sum()))
print('This many incentivized videos: {}'.format((dftmp.incentivized > 0).sum()))
print('\nThis many relevant videos by syllabus week:')
print(dftmp.syllabus_week.value_counts().sort_index())
print('\nThis many students per year:')
print(dfv[['id', 'year']].drop_duplicates().year.value_counts())


# duration per video (seconds)

# We can only observe video opens, so calculate "duration" as if every video watched
#  in its entirety. 

# Calc duration in seconds
dfv['duration'] = dfv.minutes * 60 + dfv.seconds

# Distribution of durations?
plt.hist(dfv.duration, 50)
plt.title('Distribution of video durations (seconds)')
plt.show()


# gen helpful flags
from datetime import datetime as dt

# first flag
dfv['firstflag'] = dfv.groupby(['id', 'year', 'videoid']).firstview.transform('min') == dfv.firstview

# before midterm 1
dfv['b4_mid1'] = np.array(\
                 ((dfv.year == 2018) & (dfv.firstview <= dt(2018, 10, 19, 19, 20))) | \
                 ((dfv.year == 2019) & (dfv.firstview <= dt(2019, 10, 23, 21, 20))), dtype='int')

# before midterm 2
dfv['b4_mid2'] = np.array(\
                 ((dfv.year == 2018) & (dfv.firstview <= dt(2018, 11, 19, 19, 20))) | \
                 ((dfv.year == 2019) & (dfv.firstview <= dt(2019, 11, 13, 21, 20))), dtype='int')

# before final
dfv['b4_final'] = np.array(\
                 ((dfv.year == 2018) & (dfv.firstview <= dt(2018, 12, 8, 18, 0))) | \
                 ((dfv.year == 2019) & (dfv.firstview <= dt(2019, 12, 7, 14, 30))), dtype='int')

# counts towards grade incentive
dfv['incent_counts'] = np.array(\
                       ~(dfv.b4_mid1) & (dfv.b4_final) & (dfv.incentivized >= 1), dtype='int')

# adjust incentive to int y/n
dfv['incentivized'] = np.array(dfv.incentivized >= 1, dtype='int')

for v in ['b4_mid1', 'b4_mid2', 'b4_final', 'incentivized', 'incent_counts']:
    print(dfv[v].value_counts())


# sum duration for each student: total duration, and total unique duration. 
# only keep course relevant videos.
# do this for: pre mid1, pre mid2, pre final

# init df at DeID-level
mergevars = ['id', 'year']
dfd = dfv.loc[:, mergevars].drop_duplicates()

# relevant only
print('This many videos were irrelevant: {}'.format(sum(dfv.relevant_100a == 0)))
print('This percent of videos were irrelevant: {}'.format(sum(dfv.relevant_100a == 0) / len(dfv)))
dfr = dfv.loc[dfv.relevant_100a > 0].copy()

# relevant duration, all (not unique) - before mid1, mid2, final
dfagg = dfr.copy()
dfagg['duration_mid1'] = dfagg.duration * dfagg.b4_mid1
dfagg['duration_mid2'] = dfagg.duration * dfagg.b4_mid2
dfagg['duration_final'] = dfagg.duration * dfagg.b4_final
dfaggd = dfagg.groupby(mergevars)[['duration_mid1', 'duration_mid2', 'duration_final']].agg('sum').reset_index()
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# relevant duration, unique - before mid1, mid2, final
# keep only max duration per videoid
dfaggd = dfagg.groupby(['id', 'year', 'videoid'])[['duration_mid1', 'duration_mid2', 'duration_final']].agg('max').reset_index()
dfaggd = dfaggd.groupby(mergevars)[['duration_mid1', 'duration_mid2', 'duration_final']].agg('sum').reset_index()
dfaggd.columns = ['id', 'year', 'duration_mid1_u', 'duration_mid2_u', 'duration_final_u']
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# units of hours
for v in dfd.columns[2:]:
    dfd[v] = dfd[v] / 3600

# sanity check
print('Sanity checks: should be 0 first.')
print(sum(dfd.duration_final < dfd.duration_final_u - .01))
print(sum(dfd.duration_final <= dfd.duration_final_u + .01))

# do the same thing for counts

# count all
countvars = ['b4_mid1', 'b4_mid2', 'b4_final', 'incentivized', 'incent_counts']
renamevars = ['mid1', 'mid2', 'final', 'incentivized', 'incent_counts']
dfaggd = dfr.groupby(mergevars)[countvars].agg('sum').reset_index()
display(dfaggd.head())
dfaggd.columns = mergevars + ['videos_' + x for x in renamevars]
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# count unique
dfaggd = dfr.copy()
for v in countvars:
    dfaggd[v] = dfaggd.loc[dfaggd[v] == 1, 'videoid']
dfaggd = dfaggd.groupby(mergevars)[countvars].agg('nunique').reset_index()
display(dfaggd.head())
dfaggd.columns = mergevars + ['videos_' + x + '_u' for x in renamevars]
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# sanity check
print('Sanity checks: should be 0 first.')
print(sum(dfd.videos_final < dfd.videos_final_u))
print(sum(dfd.videos_final <= dfd.videos_final_u))

display(dfd.head(3))


# ### Week-level
# 
# Collapse at the student-week level for creating time series plots

# add back students with no video watching
df = pd.read_csv("../data/generated/id-year_level_data.csv")
df['arm'] = df.toberandomized + df.treated
keepvars = ['id', 'year', 'arm', 'finalscore']
df = df[keepvars]
# display(df.head())

# Outer merge treatment status
dfv = dfv.merge(df, on=keepvars, how='outer')
dfv.head()


# Get data aggregated at id-year-week-arm level


# get week of year for each video watched
# week = 0 is week experiment began (43)
from datetime import date
dfv['weekoy'] = dfv.loc[dfv.firstview.notnull()].\
    firstview.apply(lambda x: x.isocalendar()[1]) - 43
# print(dfv.weekoy.value_counts())

# init df at id-year-weekoy-arm-level
mergevars = ['id', 'year', 'arm', 'weekoy']
muidx = pd.MultiIndex.from_product([dfv['id'].drop_duplicates(), dfv['year'].drop_duplicates(), dfv.loc[dfv.weekoy.notnull(), 'weekoy'].unique()])
dfdw = pd.DataFrame(index=muidx).reset_index()
dfdw.columns = ['id', 'year', 'weekoy']
dfdw = dfdw.merge(dfv[['id', 'year', 'arm', 'finalscore']].drop_duplicates(), on=['id', 'year'], how='inner')
dfdw.sort_values(mergevars, inplace=True)
print(len(dfdw[['id', 'year']].drop_duplicates()))
# display(dfdw.head())


# relevant videos
dfr = dfv.loc[dfv.relevant_100a == 1].copy()

# count all videos
dfaggw = dfr.groupby(mergevars)[['relevant_100a', 'duration', 'pre_mid1', 'mid1_to_mid2', 'post_mid2']].\
    agg('sum').reset_index()
dfaggw.columns = mergevars + ['videos', 'duration', 'videos_pre_mid1', 'videos_mid1_to_mid2', 'videos_post_mid2']
dfdw = dfdw.merge(dfaggw, on=mergevars, how='left')

# count unique, keeping first time watched video
dfaggwd = dfr.sort_values(['id', 'year', 'firstview']).drop_duplicates(['id', 'year', 'arm', 'videoid'])
dfaggwd = dfaggwd.groupby(mergevars)[['relevant_100a', 'duration', 'pre_mid1', 'mid1_to_mid2', 'post_mid2']].agg('sum').reset_index()
dfaggwd.columns = mergevars + ['videosu', 'durationu', 'videos_pre_mid1u', 'videos_mid1_to_mid2u', 'videos_post_mid2u']
dfdw = dfdw.merge(dfaggwd, on=mergevars, how='left')

# int cols
for c in dfdw.columns[5:]:
    # fill in zeros where appropriate
    dfdw[c] = dfdw[c].apply(lambda x: int(x) if x == x else 0)

dfdw.head()


dftmp = dfdw.groupby(['arm', 'weekoy']).agg('mean').reset_index()
for c in ['videos_pre_mid1', 'videos_mid1_to_mid2', 'videos_post_mid2']:
    plt.plot(dftmp.loc[dftmp.arm == 1].weekoy, dftmp.loc[dftmp.arm == 1, c], label='control')
    plt.plot(dftmp.loc[dftmp.arm == 2].weekoy, dftmp.loc[dftmp.arm == 2, c], label='treated')
    plt.title(c  + ', All')
    plt.legend()
    plt.show()


for c in ['videos_pre_mid1u', 'videos_mid1_to_mid2u', 'videos_post_mid2u']:
    plt.plot(dftmp.loc[dftmp.arm == 1].weekoy, dftmp.loc[dftmp.arm == 1, c], label='control')
    plt.plot(dftmp.loc[dftmp.arm == 2].weekoy, dftmp.loc[dftmp.arm == 2, c], label='treated')
    plt.title(c  + ', Unique')
    plt.legend()
    plt.show()


# checks
print(dfdw.isnull().sum())
print(len(dfdw.loc[dfdw.finalscore.isnull()].id.value_counts()))

# export
dfdw.to_csv('../data/generated/id-year-weekoy-arm_level.csv', index=False)


# ### Export

# export video data by updating the pid-year-level data

df = pd.read_csv("../data/generated/id-year_level_data.csv")
dropvars = ['videos', 'relevant', 'videos_u', 'relevant_u',
            'duration_all', 'duration_rel', 'duration_u',
            'videos_b4_mid1_rel', 'videos_b4_mid1_relu',
            'videos_b4_mid2_rel', 'videos_b4_mid2_relu', 
            'duration_mid1', 
            'duration_mid2',
            'duration_final',
            'duration_mid1_u',
            'duration_mid2_u',
            'duration_final_u',
            'videos_mid1',
            'videos_mid2',
            'videos_final',
            'videos_incentivized',
            'videos_incent_counts',
            'videos_mid1_u',
            'videos_mid2_u',
            'videos_final_u',
            'videos_incentivized_u',
            'videos_incent_counts_u']

df = df.loc[:, [c for c in df.columns if c not in dropvars]]
df.head()

# merge dfd on df and add zeros when no videos observed
df = df.merge(dfd, on=['id', 'year'], how='outer')
for c in df.columns[-23:]:
    df.loc[df[c].isnull(), c] = 0
for c in df.columns[-10:]:
    df[c] = df[c].apply(lambda x: int(x))

print(df.isnull().sum())
display(df.head())

# save csv
df.to_csv("../data/generated/id-year_level_data.csv", index=False)


df.videos_incent_counts_u.value_counts().sort_index()


# ### 100B

# import 100B video history
dfv = pd.read_csv('../data/raw/DeID_video-level_data_100b.csv')
dfv = dfv.loc[dfv.videoid.notnull()]

# keep only necessary vars
dfv = dfv[['DeID', 'year', 'visit.id', 'first.view', 'last.view', 'videoid']]

# merge duration
lengths = pd.read_excel('../data/raw/video_lengths.xlsx')
lengths = lengths[['videoid', 'minutes', 'seconds']]
lengths['duration'] = lengths.minutes * 60 + lengths.seconds
dfv = dfv.merge(lengths[['videoid', 'duration']], on='videoid', how='left')

# date columns
dfv['lastview'] = pd.to_datetime(dfv['last.view'])
dfv['firstview'] = pd.to_datetime(dfv['first.view'])

# unnecessary cols
dfv.drop(['first.view', 'last.view'], 1, inplace=True)

# rename id col
dfv.rename(columns={'DeID': 'id'}, inplace=True)

print(dfv.isnull().sum())
dfv.head(2)


# duration per video (seconds)

plt.hist(dfv.duration, 50)
plt.title('Distribution of video durations (seconds)')
plt.show()


# sum duration for each student: total duration, and total unique duration. 

# init df at DeID-level
mergevars = ['id', 'year']
dfd = dfv.loc[:, mergevars].drop_duplicates()

# relevant duration, all (not unique)
dfagg = dfv.copy()
dfaggd = dfagg.groupby(mergevars)[['duration']].agg('sum').reset_index()
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# relevant duration, unique
# keep only max duration per videoid
dfaggd = dfagg.groupby(['id', 'year', 'videoid'])[['duration']].agg('max').reset_index()
dfaggd = dfaggd.groupby(mergevars)[['duration']].agg('sum').reset_index()
dfaggd.columns = ['id', 'year', 'duration_u']
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# units of hours
for v in dfd.columns[2:]:
    dfd[v] = dfd[v] / 3600

# colnames
dfd.columns = ['id', 'year', 'duration_b', 'duration_b_u']

# sanity check
print('Sanity checks: should be 0 first.')
print(sum(dfd.duration_b < dfd.duration_b_u - .01))
print(sum(dfd.duration_b <= dfd.duration_b_u + .01))


# do the same thing for counts

# count all
dfagg['cnt'] = 1
dfaggd = dfagg.groupby(mergevars)[['cnt']].agg('sum').reset_index()
dfaggd.columns = ['id', 'year', 'videos_b']
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# count unique
dfaggd = dfv.copy()
dfaggd['videos_b_u'] = dfaggd.videoid
dfaggd = dfaggd.groupby(mergevars)[['videos_b_u']].agg('nunique').reset_index()
dfd = dfd.merge(dfaggd, on=mergevars, how='left')

# sanity check
print('Sanity checks: should be 0 first.')
print(sum(dfd.videos_b < dfd.videos_b_u))
print(sum(dfd.videos_b <= dfd.videos_b_u))

display(dfd.head(3))


# ### Export

# export video data by updating the pid-year-level data

df = pd.read_csv("../data/generated/id-year_level_data.csv")
dropvars = ['videos_b', 'relevant_b', 'videos_u_b', 
            'relevant_u_b', 'duration_all_b', 
            'duration_rel_b', 'duration_u_b']

df = df.loc[:, [c for c in df.columns if c not in dropvars]]
display(df.head(2))

# merge dfd on df and add zeros when no videos observed
df = df.merge(dfd, on=['id', 'year'], how='outer')
for c in df.columns[-4:]:
    df.loc[df[c].isnull(), c] = 0
for c in df.columns[-2:]:
    df[c] = df[c].apply(lambda x: int(x))

print(df.isnull().sum())
display(df.head())

# save csv
df.to_csv("../data/generated/id-year_level_data.csv", index=False)

