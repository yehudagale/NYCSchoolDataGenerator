# NYCSchoolDataGenerator
Uses publically available information about the school match outcomes and demographics in NYC to generate realistic datasets
# Instructions
To run simply select a year you see a folder for, and use that as the only argument to make_student_csvs_any_year.py for example:
make_student_csvs_any_year.py 2023
Once that is run, you can add demographic data such as sex, race, and test scores by running add_demographics.py $YEAR. For example:
add_demographics.py 2023
The 3 most important output files will be:

student_info_with_demographics.csv containing the demographic data and test scores of each simulated student

student_prefs.csv containing the preferences of each simulated student

temp_school.csv containing the data about the each school

# Notes
The system offers some results of the match to use to compare to the real data, these results do not take into account the simulated scores of the students, and are thus only really accurate if the match can be simulated as a lottery.
