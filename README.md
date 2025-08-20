*Automated Student Performance Reports*
==============================================================
A Python script generating personalized HTML reports & Excel rankings for entry tests (CURRENTLY IN DEVELOPMENT)
*Overview*
------------ 
This script processes mock test results to produce detailed performance reports, featuring:
📊 Charts and statistics for section-wise and topic-wise analysis
📝 Personalized feedback, tips, and motivational quotes
📈 Excel output for aggregated student data and rankings
*Key Features*
---------------- 
* Loads data from JSON files and environment variables (.env)
* Evaluates student answers, calculating metrics like accuracy and attempted questions
* Generates visually rich HTML reports with ApexCharts for performance visualization
* Saves student scores to Excel files, updating existing records or creating new ones
* Ranks students based on percentage scores, limiting to top 100 if applicable
* Includes PDF export option using html2canvas and jsPDF
*Tech Stack*
---------------- 
Python 3.x | pandas | ApexCharts | html2canvas | jsPDF | python-dotenv
*Benefits*
-------------
* Automates performance report generation, saving instructors time
* Provides personalized feedback and insights for students
* Enables data-driven decision making with Excel output and rankings

