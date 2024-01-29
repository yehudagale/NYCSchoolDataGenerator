import pandas as pd
import numpy as np
from sys import argv
rng = np.random.default_rng(seed=10)


YEAR_MARKER_2 = int(argv[1]) - 1
YEAR_MARKER = f'{YEAR_MARKER_2 - 2}-{YEAR_MARKER_2 - 2001}'

demographic_data = pd.read_csv('./starting_data_all_years/Demographic_Snapshot_2017-18_to_2021-22__Public_district.csv')
print(demographic_data.columns)
demographic_data['Grade 7'] =  demographic_data['Grade 7'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
demographic_data['Grade 7'] = demographic_data['Grade 7'].astype('int64')
print(demographic_data[['Grade 7', 'Administrative District']][demographic_data['Year'] == YEAR_MARKER])
print(demographic_data[['Grade 7', 'Administrative District']][demographic_data['Year'] == YEAR_MARKER].sum())
student_district_map_df = pd.read_csv(f'./{YEAR_MARKER_2+1}/student_info.csv')
print(len(student_district_map_df))
print(student_district_map_df.groupby(['Residential_District']).count())


demographic_data_school = pd.read_csv('./starting_data_all_years/Demographic_Snapshot_2017-18_to_2021-22__Public_.csv')
demographic_data_school['Grade 7'] =  demographic_data_school['Grade 7'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
demographic_data_school['Grade 7'] = demographic_data_school['Grade 7'].astype('int64')
demographic_data_school['Administrative District'] = demographic_data_school['DBN'].str.slice(stop=2)
print(demographic_data_school[demographic_data_school['Year'] == YEAR_MARKER].groupby(['Administrative District'])[['Grade 7', 'Administrative District']].sum())

print('-------')
def add_demographics_school_based(demograph_file, student_file):
    global fallbacks
    fallbacks = [0,0,0]
    math_score_converter = pd.read_csv('./starting_data_all_years/Math_score_conversion.csv').set_index('scale_score', drop=False)
    ela_score_converter = pd.read_csv('./starting_data_all_years/ELA_score_conversion.csv').set_index('scale_score', drop=False)
    # def replace_s(row):
    district_fallback_math_school = pd.read_csv('./starting_data_all_years/district-math-results-2013-2022-(public)_econ_status.csv').set_index('District', drop=False)
    district_fallback_math_school = district_fallback_math_school[district_fallback_math_school['Year'] == YEAR_MARKER_2]
    district_fallback_math_school = district_fallback_math_school[district_fallback_math_school['Grade'] == '7']
    district_fallback_math_school = district_fallback_math_school.replace(',','', regex=True)

    math_data_school = pd.read_csv('./starting_data_all_years/school-math-results-2013-2022-(public).csv').set_index('DBN', drop=False)
    math_data_school = math_data_school[math_data_school['Year'] == YEAR_MARKER_2]
    math_data_school = math_data_school[math_data_school['Grade'] == '7']
    math_data_school = math_data_school.replace(',','', regex=True)

    ela_data_school = pd.read_csv('./starting_data_all_years/school-ela-results-2013-2022-(public)(1).csv').set_index('DBN', drop=False)
    ela_data_school = ela_data_school[ela_data_school['Year'] == YEAR_MARKER_2]
    ela_data_school = ela_data_school[ela_data_school['Grade'] == '7']
    ela_data_school = ela_data_school.replace(',','', regex=True)

    district_fallback_ela_school = pd.read_csv('./starting_data_all_years/district-ela-results-2013-2022-(public)_econ_status.csv').set_index('District', drop=False)
    district_fallback_ela_school = district_fallback_ela_school[district_fallback_ela_school['Year'] == YEAR_MARKER_2]
    district_fallback_ela_school = district_fallback_ela_school[district_fallback_ela_school['Grade'] == '7']
    district_fallback_ela_school = district_fallback_ela_school.replace(',','', regex=True)

    swd_ela = pd.read_csv('./starting_data_all_years/school-ela-results-2013-2022-(public)_swd.csv').set_index('DBN', drop=False)
    swd_ela = swd_ela[swd_ela['Year'] == YEAR_MARKER_2]
    swd_ela = swd_ela[swd_ela['Grade'] == '7']
    swd_ela = swd_ela.replace(',','', regex=True)
    swd_ela['District'] = swd_ela['DBN'].str.slice(stop=2)

    swd_math = pd.read_csv('./starting_data_all_years/school-math-results-2013-2022-(public)_swd.csv').set_index('DBN', drop=False)
    swd_math = swd_math[swd_math['Year'] == YEAR_MARKER_2]
    swd_math = swd_math[swd_math['Grade'] == '7']
    swd_math = swd_math.replace(',','', regex=True)
    swd_math['District'] = swd_math['DBN'].str.slice(stop=2)

    ell_ela = pd.read_csv('./starting_data_all_years/school-ela-results-2013-2022-(public)_ell.csv').set_index('DBN', drop=False)
    ell_ela = ell_ela[ell_ela['Year'] == YEAR_MARKER_2]
    ell_ela = ell_ela[ell_ela['Grade'] == '7']
    ell_ela = ell_ela.replace(',','', regex=True)
    ell_ela['District'] = ell_ela['DBN'].str.slice(stop=2)

    ell_math = pd.read_csv('./starting_data_all_years/school-math-results-2013-2022-(public)_ell.csv').set_index('DBN', drop=False)
    ell_math = ell_math[ell_math['Year'] == YEAR_MARKER_2]
    ell_math = ell_math[ell_math['Grade'] == '7']
    ell_math = ell_math.replace(',','', regex=True)
    ell_math['District'] = ell_math['DBN'].str.slice(stop=2)


    demography_df = pd.read_csv(demograph_file)
    demography_df = demography_df[demography_df['Year'] == YEAR_MARKER]
    demography_df = demography_df.replace(',','', regex=True)#applymap(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
    # demography_df['Grade 7'] =  demography_df['Grade 7'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
    demography_df['Grade 7'] = demography_df['Grade 7'].astype('int32')
    demography_df = demography_df[demography_df['Grade 7'] > 0]
    demography_df['Administrative District'] = demography_df['DBN'].str.slice(stop=2)
    demography_df = demography_df[demography_df['Administrative District'] != '84']
    demography_df = demography_df[demography_df['Administrative District'] != '75']
    totals = demography_df[demography_df['Year'] == YEAR_MARKER].groupby(['Administrative District'])[['Grade 7', 'Administrative District']].sum()
    totals = totals.rename({'Grade 7':'district size'}, axis=1)
    # totals.set_index('Administrative District')
    demography_df = demography_df.join(totals, on='Administrative District')
    # demography_df['Total Enrollment'] =  demography_df['Total Enrollment'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
    demography_df['Total Enrollment'] = demography_df['Total Enrollment'].astype('int32')
    # print(demography_df[['district size', 'Administrative District']])
    demography_df['weights'] = demography_df['Grade 7'] / demography_df['district size']

    econ_status = {0:'Not Econ Disadv', 1:'Econ Disadv'}
    swd_status = {0:'Not SWD', 1:'SWD'}
    #now we are ready to start adding information for inidvidual students
    def add_student_demographics(district):

        global fallbacks
        def get_school(schools, fallback, DBN, district, demographics, swd_data, ell_data):
            if DBN in schools.index:
                temp_school = schools.loc[DBN]
                fallbacks[0] += 1
                # print(temp_school)
                # exit(0)
                ell_school = ell_data[(ell_data['DBN'] == DBN) & (ell_data['Category'] == 'Never ELL') ].squeeze()
                swd_school = swd_data[(swd_data['DBN'] == DBN) & (swd_data['Category'] == 'Not SWD') ].squeeze()
                # print(swd_school)
                if (not swd_school.empty) and swd_school['# Level 4'] != 's':
                    swd_school = swd_school[['Number Tested', '# Level 1', '# Level 2', '# Level 3', '# Level 4']].astype('int32')
                    temp_school = temp_school[['Number Tested', '# Level 1', '# Level 2', '# Level 3', '# Level 4']].astype('int32')
                    if demographics['swd']:
                        # print(temp_school, swd_school)
                        temp_school = temp_school - swd_school
                        # print(temp_school)
                        # exit(0)
                    elif (not demographics['ell']) or (ell_school.empty) :
                        temp_school = swd_school
                # print(ell_school)
                if (not ell_school.empty) and ell_school['# Level 4'] != 's' and demographics['ell'] and not demographics['swd']:
                    ell_school = ell_school[['Number Tested', '# Level 1', '# Level 2', '# Level 3', '# Level 4']].astype('int32')
                    temp_school = temp_school[['Number Tested', '# Level 1', '# Level 2', '# Level 3', '# Level 4']].astype('int32')
                    # print(temp_school, ell_school)
                    # print(demographics)
                    temp_school = temp_school - ell_school
                    # print(temp_school)
                    # exit(0)
                if temp_school['Number Tested'] == 0:
                    temp_school['# Level 4'] = 's'
                    # temp_school = temp_school - demographics['swd'] * swd_school
            else:
                # print(f'Fallback {DBN}')
                temp_school = fallback[(fallback['District'] == int(district)) & (fallback['Category'] == econ_status[demographics['poverty']]) ].squeeze()
                fallbacks[1] += 1
            try:
                if temp_school['# Level 4'] == 's':
                    # print(f'Fallback s {DBN}')
                    temp_school = fallback[(fallback['District'] == int(district)) & (fallback['Category'] == econ_status[demographics['poverty']]) ].squeeze()
                    fallbacks[2] += 1
            except ValueError as v:
                print(v)
                print(temp_school)
                raise v
            return temp_school



        #first we will select which school they went to in eight grade
        # print(district)
        district = district['Residential_District'][-2:]
        #in case we don't know the district, select from all schools
        if district != 'wn':
            temp_df = demography_df[demography_df['Administrative District'] == district]
        else:
            temp_df = demography_df
        if rng.random() < 0.001:
            print(district)
        if temp_df.empty:
            print(district)
        school = temp_df.sample(weights=temp_df['Grade 7']).iloc[0]
        if district == 'wn':
            district = school['DBN'][:2]
        # print(math_data_school.loc['01M140'])

        # print(school)
        #then we will draw their demographics from the demographics of that school
        #small helper function to get demographic from number of students with that charecteristic:

        def get_demographic_char(have_char, total):
            if isinstance(have_char, str):
                have_char = have_char.replace(',', '')
            try:
                have_char = int(have_char)
            except ValueError as e:
                if 'Above' in have_char:
                    have_char = total
                else:
                    raise e
            return 1 if rng.random() < have_char/total else 0
        def process_eni(item):
            last_word = item.split()[-1]
            return float(last_word[:-1]) / 100
        def process_ethnicity(school, ethnicities, total):
            return rng.choice(ethnicities, p=[int(school[f'# {ethnicity}'])/total for ethnicity in ethnicities])
        def process_scores(school, scores, total, converter):
            perf_level = rng.choice(scores, p=[int(school[f'# Level {score}'])/total for score in scores])
            temp_perf = 0
            while temp_perf != perf_level:
                scaled = int(np.round(rng.normal(600, 20)))
                if scaled in converter.index:
                    # print(perf_level, scaled)
                    row = converter.loc[scaled]
                    temp_perf = row['perf_level']
                    score = row['exact_score']
            return score


        total_students = int(school['Total Enrollment'])
        demography_dict = {'swd':get_demographic_char(school['# Students with Disabilities'],total_students), 'poverty':get_demographic_char(school['# Poverty'],total_students), 'sex':get_demographic_char(school['# Female'],total_students), 'ell':get_demographic_char(school['# English Language Learners'],total_students), 'ENI':process_eni(school['Economic Need Index'])}
        ethnicities = ['Black', 'Hispanic', 'Multi-Racial', 'White', 'Asian', 'Native American', 'Missing Race/Ethnicity Data']
        scores = [1,2,3,4]
        # for ethnicity in ethnicities:
        #     demography_dict[ethnicity] = get_demographic_char(school[f'# {ethnicity}'],total_students)
        chosen_ethnicity = process_ethnicity(school, ethnicities, total_students)
        # exit(0)
        ethnicity_dict = {ethnicity:0 for ethnicity in ethnicities}
        demography_dict.update(ethnicity_dict)
        demography_dict[chosen_ethnicity] = 1
        demography_dict['school'] = school['DBN']

        math_school = get_school(math_data_school, district_fallback_math_school, school['DBN'], district, demography_dict, swd_math, ell_math)
        ELA_school = get_school(ela_data_school, district_fallback_ela_school, school['DBN'], district, demography_dict, swd_ela, ell_ela)
        chosen_math_score = process_scores(math_school,scores,math_school['Number Tested'], math_score_converter)
        ela_score = process_scores(ELA_school,scores,ELA_school['Number Tested'], ela_score_converter)

        demography_dict['Math_score'] = chosen_math_score
        demography_dict['ELA_score'] = ela_score

        # demography_dict['fallback_for_scores'] =
        # demography_dict['unkown'] = get_demographic_char(school[f'# Missing Race/Ethnicity Data'],total_students)
        # print(demography_dict)
        return pd.Series(demography_dict)
    #Lets add some demography to the students
    #letss select from district 01
    student_info = pd.read_csv(student_file)
    print(student_info)
    student_info = student_info[::-1]
    demographics = student_info.apply(add_student_demographics, axis=1)
    print(demographics)
    student_info.join(demographics).to_csv(f'{YEAR_MARKER_2 + 1}/student_info_with_demographics.csv', index=False)
    # rng.choice(list(bucket), p=[bucket[key]/total for key in bucket])
add_demographics_school_based('./starting_data_all_years/Demographic_Snapshot_2017-18_to_2021-22__Public_.csv', f'./{YEAR_MARKER_2+1}/student_info.csv')
print(fallbacks)
