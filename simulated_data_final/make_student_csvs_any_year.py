#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import sys
import pickle
from copy import deepcopy
from sys import argv
from gale_shapley import Multi_Slot, Single_Slot, gale_shapley_algorithm

NUM_CHOICES = 12
rng = np.random.default_rng(seed=7)

YEAR = int(argv[1])
# DISTRICT_FILE = f'./{YEAR}/starting_data/{YEAR}_Fall_district.csv'
SCHOOL_FILE = f'./{YEAR}/starting_data/{YEAR}_Fall_school.csv'
HAVE_RESULTS = False
# # Cleaning data


# The first step is to clean the data.
#
# I will start with the school data removing schools we don't have enough information about to use (including the special schools) and only using the high school data

# In[2]:


replace_on_row = lambda x : rng.integers(low=0, high=5, endpoint=True) if x == 's' else x
def replace_s(row):
    if row['Category'] == 'All Students':
        return row.apply(replace_on_row)
    else:
        return row
def replace_high_s(row):
    if row['Category'] == 'All Students':
        if row['Grade 9 Offers'] == 's^':
            row['Grade 9 Offers'] = row['Grade 9 True Applicants']
            return row
        else:
            return row
    else:
        return row
def clean_one_year_data(file_name):
    def first_letter_cap(word):
        split = word.split()
        return ' '.join([f'{word[0].upper()}{word[1:]}' for word in split])
    data = pd.read_csv(file_name).replace(',','', regex=True)
    data = data.rename(first_letter_cap, axis=1)
    print(data.columns)
    if "Grade 9 Applicants" not in data.columns:
    	data["Grade 9 Applicants"] = data['Grade 9 Total Applicants']
    data.dropna(subset=["Grade 9 Applicants"], inplace=True)
    data.sort_values(by=["School Name", "Category"], inplace=True)
    print(data.columns)
    if 'Grade 9 True Applicants' in data.columns:
        data = data.loc[:,['School District', 'School DBN', 'School Name', 'Category','Grade 9 Seats Available', 'Grade 9 Applicants', 'Grade 9 Offers','Grade 9 True Applicants']]
    else:
        data = data.loc[:,['School District', 'School DBN', 'School Name', 'Category','Grade 9 Seats Available', 'Grade 9 Applicants', 'Grade 9 Offers']]
    # data.drop(labels = ['Pre-K Seats Available', 'Pre-K Applicants', 'Pre-K Offers',
    #    'Kindergarten Seats Available', 'Kindergarten Applicants',
    #    'Kindergarten Offers', 'Grade 6 Seats Available', 'Grade 6 Applicants',
    #    'Grade 6 Offers'], axis=1, inplace=True)
    data['Grade 9 Seats Available - Notes'] = data['Grade 9 Seats Available'].apply(lambda x :  x.split(';')[1] if isinstance(x, str) and ';' in x else None)
    data['Grade 9 Seats Available'] = data['Grade 9 Seats Available'].apply(lambda x :  x.split(';')[0] if isinstance(x, str) else x)
    # data['Grade 9 Offers'] =  data['Grade 9 Offers'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
    # data['Grade 9 Seats Available'] =  data['Grade 9 Seats Available'].apply(lambda x :  x.replace(',', '') if isinstance(x, str) else x)
    data['Grade 9 Offers'] =  data['Grade 9 Offers'].apply(lambda x :  None if x == 'N/A' else x)
    data['Grade 9 Seats Available'] =  data['Grade 9 Seats Available'].apply(lambda x :  None if x in ['N/A', '0', 0] else x)
    #For now, we will simply replace s with a random number between 0 and 5, but we need to be careful to only replace the low impact s's (this ones from the whole school section)
#     data = data.astype({'School District':'int32', 'Grade 9 Seats Available':'int32', 'Grade 9 Applicants':'int32',
#        'Grade 9 Offers':'int32', })
    # data = data.loc[data['Grade 9 Seats Available'] != 0]
    return data


# In[3]:


real_data = clean_one_year_data(SCHOOL_FILE)

#now we take only the "all students" rows (though the next step drops any other rows anyway)
school_data = real_data.loc[real_data['Category'] == 'All Students'].copy()
#find all the schools we are dropping
school_data.loc[pd.isna(school_data['Grade 9 Seats Available'])].to_csv(f'{YEAR}/dropped_schools.csv')
school_data = school_data.dropna(subset=['Grade 9 Seats Available', 'Grade 9 Offers'])
if 'Grade 9 True Applicants' in school_data.columns:
    school_data.loc[pd.isna(school_data['Grade 9 True Applicants'])].to_csv(f'{YEAR}/dropped_schools.csv')
    school_data = school_data.dropna(subset=['Grade 9 True Applicants', 'Grade 9 Seats Available', 'Grade 9 Offers'])

#find all the schools we are changing s in
school_data[school_data.isin(['s']).any(axis=1)].to_csv(f'{YEAR}/s_schools.csv')

school_data = school_data.apply(replace_s, axis=1)
school_data = school_data.apply(replace_high_s, axis=1)
print(school_data.columns)
school_data['Grade 9 Seats Available'] = school_data['Grade 9 Seats Available'].astype('int64')



school_data['Grade 9 Offers'] = school_data['Grade 9 Offers'].astype('int64')
print(school_data['Grade 9 Offers'].sum())
print(school_data.loc[:,['Grade 9 Seats Available', 'Grade 9 Offers']])


# We need to guess about the capacity. When the number of offers is higher than the seats available then we know that is the correct capacity. However, sometimes, less popular schools may not get enough chances in the gale-shapley algorithm to make as many offers as they have seats, so to account for that we use number of seats available column when it is higher than the offers column

# In[4]:


school_data['max_offers_and_seats'] = school_data.loc[:,['Grade 9 Seats Available', 'Grade 9 Offers']].max(axis=1)
#export to csv for easier veiwing later
school_data.to_csv(f'{YEAR}/temp_school.csv')


# Now we need to clean the student data set, we will try to make as few assumtions as possible. First we need to get the number of students and number of applications per a residential district

# In[5]:

# if HAVE_RESULTS:
header_size = {2022:5, 2020:1, 2019:3, 2023:5}
student_number_df = pd.read_csv(f"./{YEAR}/starting_data/fall-{YEAR}-high-school-offer-results.csv",\
        usecols=[0,1,2,3,4,5,6],\
        names =['Residential District', 'Total Applicants', '# Matches to Choice 1-3','# Matches to Choice 1-5', '# Matches to Choice 1-10','# Matches to Choice 1-12', '# Matches to Any Choice (Incl. SHS & LGA)']\
        , skiprows=header_size[YEAR]).replace(',','', regex=True)
#read and proccess the number of applicants per district into a dictionary for use
applicant_numbers = {'Residential District ' + district['Residential District'].strip().zfill(2):int(district['Total Applicants']) for i, district in student_number_df.iterrows()}
match_number = {'Residential District ' + district['Residential District'].strip().zfill(2):int(district['# Matches to Choice 1-12']) for i, district in student_number_df.iterrows()}
unmatch_number = {district : applicant_numbers[district] - match_number[district] for district in applicant_numbers}
print(applicant_numbers)
num_students = applicant_numbers['Residential District Total']
# In[6]:


def make_district_buckets(school_df, student_df):
    district_buckets = {}
    for _, school in school_df.iterrows():
        total = int(school['Grade 9 Applicants'])
        school_id = school['School DBN']
        districts = student_df.loc[student_df['School DBN'] == school_id, :]
        temp_bucket = {}
        #num_s is the number of students marked with an s (between 1-5 students hidden for redaction)
        #num_big_s is the number of studnets makred with s^ (any number of students redacted due to other problems)
        num_s = 0
        num_big_s = 0
        for _, district in districts.iterrows():
            num_apps = district['Grade 9 Applicants']
            if num_apps not in ['s', 's^']:
                num_apps = int(num_apps)
                total -= int(num_apps)
            elif num_apps == 's':
                num_s += 1
            else:
                num_big_s += 1
            temp_bucket[district['Category']] = num_apps
        #split the remainder eqauly between the small districts
        #first give up to 5 to each district marked with s

        # lets say we have 10 seats left and 3 s's
        # 10 // 3 = 3
        # s_remain = 1
        # 4
        # first s gets 4 seats
        # second s gets 3 seats
        # third s gets 3 seats

        if num_s:
            #give out 1 extra until the remainder is used up to exactly use up the total
            s_num = (total // num_s) + 1
            s_remain = total % num_s
            if s_num > 5:
                s_num = 5
            for key in temp_bucket:
                if temp_bucket[key] == 's':
                    if s_remain == 0:
                        s_num -= 1
                    s_remain -= 1
                    temp_bucket[key] = s_num
                    total -= s_num
        if num_big_s:
            s_num = total // num_big_s
            for key in temp_bucket:
                if temp_bucket[key] == 's^':
                    temp_bucket[key] = s_num
                    total -= s_num
        for district in temp_bucket:
            if district not in district_buckets:
                district_buckets[district] = {}
                district_buckets[district]['total'] = 0
            if temp_bucket[district] > 0:
                district_buckets[district][school_id] = temp_bucket[district]
                district_buckets[district]['total'] += temp_bucket[district]

    return district_buckets
#first read all rows that are related to a Residential district
student_data = real_data.loc[real_data['Category'].str.contains('Residential')]
student_data.to_csv(f'{YEAR}/temp_students.csv')
district_buckets = make_district_buckets(school_data, student_data)
district_totals = {district:district_buckets[district]['total'] for district in district_buckets}
district_buckets = {key:district_buckets[key] for key in district_buckets if key in applicant_numbers}
for district in district_buckets:
    del district_buckets[district]['total']

with open(f'{YEAR}/district_prefs.csv', 'w') as d_prefs:
    d_prefs.write('district,school,num_applications\n')
    for district in district_buckets:
        for school in district_buckets[district]:
            d_prefs.write(f'{district},{school},{district_buckets[district][school]}\n')

# Lastly we need the mean number of applicants per student for each district

# In[7]:


district_means = {key:district_totals[key] /applicant_numbers[key] for key in district_buckets}
print(district_means)


# Now lets finally make the student and school objects for gale-shaply
#

# In[8]:


#NOTE: this is one of the main assumtions in this model, the std deviation of the number of schools each student applies to
STD_DEV = np.std([district_means[key] for key in district_means])
# for residentail district 5 school A 50 school B 10 School C 40 applicants
# for residentail district 5 school A 50 school B 10 applicants
def generate_choice(bucket, total):
    return rng.choice(list(bucket), p=[bucket[key]/total for key in bucket])

def make_student_with_replacement_limited_apps(bucket, total, app_dist):
    prefs = []
    temp_bucket = {key: bucket[key] for key in bucket}
    temp_total = total
    app_num = int(round(rng.normal(app_dist, STD_DEV)))

    app_num = np.clip(app_num, 1, int(NUM_CHOICES))
    # if rng.integers(0,1000) == 0:
    #     print(app_num)
    for x in range(app_num):
        choice = generate_choice(temp_bucket, temp_total)
        prefs.append(choice)
        temp_total -= temp_bucket[choice]
        del temp_bucket[choice]
    return Single_Slot(ID, prefs), bucket, total
#first the school objects
student_ids = [f'student_{i}' for i in range(num_students)]

#Now the student objects
students = student_ids.copy()
rng.shuffle(students)
student_objs = []
district_buckets = make_district_buckets(school_data, student_data)
district_totals = {district:district_buckets[district]['total'] for district in district_buckets}
for district in district_buckets:
    del district_buckets[district]['total']
student_district_map = {}
for district in applicant_numbers:
    # print(district)
    if district in district_buckets:
        for x in range(applicant_numbers[district]):
            ID = students.pop()
            student_district_map[ID] = district
            student, district_buckets[district], total = make_student_with_replacement_limited_apps(district_buckets[district],  district_totals[district], district_means[district])
            student_objs.append(student)
#dump the objects with pickle for later
# pickle.dump((student_objs, schools), open('./real_data_random_order_applicant_count_varying_districts.p', 'wb'))


# # Experiments
# Now that we have a cleaned database we can run some actual experiments
#
# In each experiment we will reload the students and schools from a file to make it easier to rerun individual experiments

# In[9]:


# students, schools = pickle.load(open('real_data_random_order_applicant_count_varying_districts.p', 'rb'))
print('Max offers and seats available')
students = deepcopy(student_objs)
schools = [Multi_Slot(row['School DBN'], student_ids, int(row['max_offers_and_seats'])) for i, row in school_data.iterrows()]
print(students[0].prefs)
# school_id = [school.id for school in schools]
students_max, schools = gale_shapley_algorithm(students, schools)
print(len(schools[0].prefs))
print(f'num students is {len(students_max)}')
capacity = sum([school.capacity for school in schools])
print(f'total capacity is {capacity}')
unmatched = [student for student in students_max if student.current_match == None]
print(f'unmatched {len(unmatched)} percent is {100 - 100 * len(unmatched) / len(students)} % ')
print(f'this compares to the actual numbers of unmatched {unmatch_number["Residential District Total"]} which is {100 - 100 * unmatch_number["Residential District Total"] / len(students_max)} % ')


# Lets see the unmatched breakdown by district

# In[10]:


by_district = {key:0 for key in district_means}
for student in unmatched:
    by_district[student_district_map[student.id]] += 1
results = [(by_district[district]/applicant_numbers[district], district) for district in by_district]
results = sorted(results, reverse=True)
total_squared_error = 0
num_items = 0
for result in results:
    print('-----------')
    district = result[1]
    print(f'In {district} there were {by_district[district]} unmatched students out of {applicant_numbers[district]} total students')
    print(f'Students in this district applied to {district_means[district]} schools on average')
    print(f'this lead to {100 - 100*by_district[district]/applicant_numbers[district]}% match rate')
    print(f'compared to the actual results of {unmatch_number[district]} unmatched students which is {100 - 100*unmatch_number[district]/applicant_numbers[district]} %')
    total_squared_error += (unmatch_number[district] - by_district[district]) ** 2
    num_items += 1



# In[ ]:


print(total_squared_error / num_items)



# # Now lets try using only offers instead of the max
#
# # In[12]:
#
#
# students, _ = pickle.load(open('real_data_random_order_applicant_count_varying_districts.p', 'rb'))
print("Seats Available")
students = deepcopy(student_objs)
print(students[0].prefs)
schools = [Multi_Slot(row['School DBN'], student_ids, int(row['Grade 9 Seats Available'])) for i, row in school_data.iterrows()]
students, schools = gale_shapley_algorithm(students, schools)
print(students[0].prefs)
print(len(schools[0].prefs))
print(f'num students is {len(students)}')
capacity = sum([school.capacity for school in schools])
print(f'total capacity is {capacity}')
unmatched = [student for student in students if student.current_match == None]
print(f'unmatched {len(unmatched)} percent is {100 - 100 * len(unmatched) / len(students)} % ')
print(f'this compares to the actual numbers of unmatched {unmatch_number["Residential District Total"]} which is {100 - 100 * unmatch_number["Residential District Total"] / len(students)} % ')
by_district = {key:0 for key in district_means}
total_squared_error = 0
num_items = 0
for student in unmatched:
    by_district[student_district_map[student.id]] += 1
results = [(by_district[district]/applicant_numbers[district], district) for district in by_district]
results = sorted(results, reverse=True)
for result in results:
    print('-------')
    district = result[1]
    print(f'In {district} there were {by_district[district]} unmatched students out of {applicant_numbers[district]} total students')
    print(f'Students in this district applied to {district_means[district]} schools on average')
    print(f'this lead to {100 - 100*by_district[district]/applicant_numbers[district]}% match rate')
    print(f'compared to the actual results of {unmatch_number[district]} unmatched students which is {100 - 100*unmatch_number[district]/applicant_numbers[district]} %')
    total_squared_error += (unmatch_number[district] - by_district[district]) ** 2
    num_items += 1
print(total_squared_error / num_items)
with open(f'{YEAR}/match_results_available.csv', 'w') as results:
    results.write('Student_Id,School\n')
    for student in students:
        results.write(f'{student.id},{student.current_match}\n')

with open(f'{YEAR}/match_outcomes_available.csv', 'w') as out:
    less_than_3 = {key:0 for key in by_district}
    less_than_5 = {key:0 for key in by_district}
    less_than_10 = {key:0 for key in by_district}
    any = {key:0 for key in by_district}
    less_than_3_total = 0
    less_than_5_total = 0
    less_than_10_total = 0
    any_total = 0
    for student in students:
        if student.current_match:
            index = student.prefs.index(student.current_match.id)
            if index < 3:
                less_than_3[student_district_map[student.id]] += 1
                less_than_3_total += 1
            if index < 5:
                less_than_5[student_district_map[student.id]] += 1
                less_than_5_total += 1
            if index < 10:
                less_than_10[student_district_map[student.id]] += 1
                less_than_10_total += 1
            any[student_district_map[student.id]] += 1
            any_total += 1
    out.write('Residential District,Total Applicants,# Matches to Choice 1-3,# Matches to Choice 1-5,# Matches to Choice 1-10,# Matches to Choice 1-12,# Matches to Any Choice (Incl. SHS & LGA),% Matches to Choice 1-3,% Matches to Choice 1-5,% Matches to Choice 1-10,% Matches to Choice 1-12,% Matches to Any Choice (Incl. SHS & LGA)\n')
    for district in less_than_5:
            out.write(f'{district},{applicant_numbers[district]},{less_than_3[district]},{less_than_5[district]},{less_than_10[district]},{any[district]},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3[district] / applicant_numbers[district]) * 100)}%,{round((less_than_5[district] / applicant_numbers[district]) * 100)}%,{round((less_than_10[district] / applicant_numbers[district]) * 100)}%,{round((any[district] / applicant_numbers[district]) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')
    out.write(f'Total,{len(students)},{less_than_3_total},{less_than_5_total},{less_than_10_total},{any_total},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3_total / len(students)) * 100)}%,{round((less_than_5_total /  len(students)) * 100)}%,{round((less_than_10_total /  len(students)) * 100)}%,{round((any_total /  len(students)) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')

print("offers")
students = deepcopy(student_objs)
print(students[0].prefs)
schools = [Multi_Slot(row['School DBN'], student_ids, int(row['Grade 9 Offers'])) for i, row in school_data.iterrows()]
students, schools = gale_shapley_algorithm(students, schools)
print(students[0].prefs)
print(len(schools[0].prefs))
print(f'num students is {len(students)}')
capacity = sum([school.capacity for school in schools])
print(f'total capacity is {capacity}')
unmatched = [student for student in students if student.current_match == None]
print(f'unmatched {len(unmatched)} percent is {100 - 100 * len(unmatched) / len(students)} % ')
print(f'this compares to the actual numbers of unmatched {unmatch_number["Residential District Total"]} which is {100 - 100 * unmatch_number["Residential District Total"] / len(students)} % ')
by_district = {key:0 for key in district_means}
for student in unmatched:
    by_district[student_district_map[student.id]] += 1
results = [(by_district[district]/applicant_numbers[district], district) for district in by_district]
results = sorted(results, reverse=True)
total_squared_error = 0
for result in results:
    print('-------')
    district = result[1]
    print(f'In {district} there were {by_district[district]} unmatched students out of {applicant_numbers[district]} total students')
    print(f'Students in this district applied to {district_means[district]} schools on average')
    print(f'this lead to {100 - 100*by_district[district]/applicant_numbers[district]}% match rate')
    print(f'compared to the actual results of {unmatch_number[district]} unmatched students which is {100 - 100*unmatch_number[district]/applicant_numbers[district]} %')
    total_squared_error += (unmatch_number[district] - by_district[district]) ** 2
print(total_squared_error / num_items)
with open(f'{YEAR}/match_outcomes_offers.csv', 'w') as out:
    less_than_3 = {key:0 for key in by_district}
    less_than_5 = {key:0 for key in by_district}
    less_than_10 = {key:0 for key in by_district}
    any = {key:0 for key in by_district}
    less_than_3_total = 0
    less_than_5_total = 0
    less_than_10_total = 0
    any_total = 0
    for student in students:
        if student.current_match:
            index = student.prefs.index(student.current_match.id)
            if index < 3:
                less_than_3[student_district_map[student.id]] += 1
                less_than_3_total += 1
            if index < 5:
                less_than_5[student_district_map[student.id]] += 1
                less_than_5_total += 1
            if index < 10:
                less_than_10[student_district_map[student.id]] += 1
                less_than_10_total += 1
            any[student_district_map[student.id]] += 1
            any_total += 1
    out.write('Residential District,Total Applicants,# Matches to Choice 1-3,# Matches to Choice 1-5,# Matches to Choice 1-10,# Matches to Choice 1-12,# Matches to Any Choice (Incl. SHS & LGA),% Matches to Choice 1-3,% Matches to Choice 1-5,% Matches to Choice 1-10,% Matches to Choice 1-12,% Matches to Any Choice (Incl. SHS & LGA)\n')
    for district in less_than_5:
            out.write(f'{district},{applicant_numbers[district]},{less_than_3[district]},{less_than_5[district]},{less_than_10[district]},{any[district]},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3[district] / applicant_numbers[district]) * 100)}%,{round((less_than_5[district] / applicant_numbers[district]) * 100)}%,{round((less_than_10[district] / applicant_numbers[district]) * 100)}%,{round((any[district] / applicant_numbers[district]) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')
    out.write(f'Total,{len(students)},{less_than_3_total},{less_than_5_total},{less_than_10_total},{any_total},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3_total / len(students)) * 100)}%,{round((less_than_5_total /  len(students)) * 100)}%,{round((less_than_10_total /  len(students)) * 100)}%,{round((any_total /  len(students)) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')
with open(f'{YEAR}/match_outcomes_both.csv', 'w') as out:
    less_than_3 = {key:0 for key in by_district}
    less_than_5 = {key:0 for key in by_district}
    less_than_10 = {key:0 for key in by_district}
    any = {key:0 for key in by_district}
    less_than_3_total = 0
    less_than_5_total = 0
    less_than_10_total = 0
    any_total = 0
    for student in students_max:
        if student.current_match:
            index = student.prefs.index(student.current_match.id)
            if index < 3:
                less_than_3[student_district_map[student.id]] += 1
                less_than_3_total += 1
            if index < 5:
                less_than_5[student_district_map[student.id]] += 1
                less_than_5_total += 1
            if index < 10:
                less_than_10[student_district_map[student.id]] += 1
                less_than_10_total += 1
            any[student_district_map[student.id]] += 1
            any_total += 1
    out.write('Residential District,Total Applicants,# Matches to Choice 1-3,# Matches to Choice 1-5,# Matches to Choice 1-10,# Matches to Choice 1-12,# Matches to Any Choice (Incl. SHS & LGA),% Matches to Choice 1-3,% Matches to Choice 1-5,% Matches to Choice 1-10,% Matches to Choice 1-12,% Matches to Any Choice (Incl. SHS & LGA)\n')
    for district in less_than_5:
            out.write(f'{district},{applicant_numbers[district]},{less_than_3[district]},{less_than_5[district]},{less_than_10[district]},{any[district]},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3[district] / applicant_numbers[district]) * 100)}%,{round((less_than_5[district] / applicant_numbers[district]) * 100)}%,{round((less_than_10[district] / applicant_numbers[district]) * 100)}%,{round((any[district] / applicant_numbers[district]) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')
    out.write(f'Total,{len(students)},{less_than_3_total},{less_than_5_total},{less_than_10_total},{any_total},# Matches to Any Choice (Incl. SHS & LGA),{round((less_than_3_total / len(students)) * 100)}%,{round((less_than_5_total /  len(students)) * 100)}%,{round((less_than_10_total /  len(students)) * 100)}%,{round((any_total /  len(students)) * 100)}%,% Matches to Any Choice (Incl. SHS & LGA)\n')


with open(f'{YEAR}/student_prefs.csv', 'w') as prefs:
    with open(f'{YEAR}/match_results_offers.csv', 'w') as results:
        with open(f'{YEAR}/student_info.csv', 'w') as student_info:
            student_info.write('Student_Id,Residential_District\n')
            prefs.write('Student_Id,School,Rank,Rating\n')
            results.write('Student_Id,School\n')
            for student in students:
                student_info.write(f'{student.id},{student_district_map[student.id]}\n')
                for i,pref in enumerate(student.prefs):
                        prefs.write(f'{student.id},{pref},{i},{1/(i + 1)}\n')
                results.write(f'{student.id},{student.current_match}\n')




#
#
# # In[ ]:
#
#
#
#
#
# # In[ ]:
#
#
#
#
#
# # In[ ]:
#
#
#
#
#
# # In[ ]:
#
#
#
#
#
# # In[ ]:
