import glob
import json
import os
import re
from datetime import datetime
import random
import secrets  # Replace 'import random' with this
from dotenv import load_dotenv
import pandas as pd  # Add this line

# Load environment variables from .env file
load_dotenv()

# Load configuration from .env
REPORT_TITLE = os.getenv('REPORT_TITLE', 'MUET Entry Test Performance Report')
TEST_NAME = os.getenv('TEST_NAME', 'MUET Entry Test')
TEST_DATE = os.getenv('TEST_DATE', 'May 24, 2025')
REPORT_TIME = os.getenv('REPORT_TIME', '06:48 PM PKT on Thursday, June 05, 2025')
METADATA_PATH = os.getenv('METADATA_PATH', '../Report Genrator Scripts/metadata_mock_test_16.json')
QUESTIONS_PATH = os.getenv('QUESTIONS_PATH', '../Report Genrator Scripts/questions.json')
QUOTES_PATH = os.getenv('QUOTES_PATH', 'quotes.json')

def load_metadata(metadata_path):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_questions(questions_path):
    with open(questions_path, 'r', encoding='utf-8') as f:
        return {q['id']: q for q in json.load(f)}

def load_quotes(quotes_path):
    try:
        with open(quotes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default quotes if quotes.json is not found
        return {
            'low': [
                "Every small step forward is progress—keep going! - Unknown",
                "Challenges are just opportunities in disguise. Take them on! - Unknown",
                "The journey of a thousand miles begins with one step. - Lao Tzu"
            ],
            'moderate': [
                "You're halfway there—keep pushing forward! - Unknown",
                "Success is the sum of small efforts, repeated day in and day out. - Robert Collier",
                "Believe in yourself; you're stronger than you think! - Unknown"
            ],
            'high': [
                "Excellent work! Keep shining—you've got this! - Unknown",
                "The only way to do great work is to love what you do. - Steve Jobs",
                "You're unstoppable—maintain that momentum! - Unknown"
            ]
        }

# def assess_performance(student_data, questions, metadata):
#     total_questions = metadata['total_questions']
#     attempted = 0
#     correct = 0
#     incorrect = 0
#     skipped = 0
#     answers = {}
#
#     for answer in student_data.get('answers', []):
#         q_id = answer['id']
#         if q_id in questions:
#             student_answer = answer.get('selected_option', 'skipped')
#             correct_answer = questions[q_id]['answer']
#             correctness = 'correct' if student_answer == correct_answer else 'incorrect' if student_answer != 'skipped' else 'skipped'
#             answers[q_id] = {
#                 'selected_option': student_answer,
#                 'correctness': correctness
#             }
#             if student_answer != 'skipped':
#                 attempted += 1
#                 if student_answer == correct_answer:
#                     correct += 1
#                 else:
#                     incorrect += 1
#             else:
#                 skipped += 1
#
#     return {
#         'summary': {'total_questions': total_questions, 'attempted': attempted, 'correct': correct, 'incorrect': incorrect, 'skipped': skipped},
#         'answers': answers
#     }
def assess_performance(student_data, questions, metadata):
    total_questions = metadata['total_questions']
    attempted = 0
    correct = 0
    incorrect = 0
    skipped = 0
    answers = {}

    for answer in student_data.get('answers', []):
        q_id = answer['id']
        if q_id in questions:
            student_answer = answer.get('selected_option', 'skipped')
            correct_answer = questions[q_id]['answer']
            correctness = 'correct' if student_answer == correct_answer else 'incorrect' if student_answer != 'skipped' else 'skipped'
            answers[q_id] = {
                'selected_option': student_answer,
                'correctness': correctness
            }
            if student_answer != 'skipped':
                attempted += 1
                if student_answer == correct_answer:
                    correct += 1
                else:
                    incorrect += 1
            else:
                skipped += 1

    return {
        'summary': {'total_questions': total_questions, 'attempted': attempted, 'correct': correct, 'incorrect': incorrect, 'skipped': skipped},
        'answers': answers
    }

def generate_stats(performance, metadata):
    section_stats = {}
    topic_stats = {}
    for section, data in metadata['sections'].items():
        start, end = data['range']
        section_answers = [a for q_id, a in performance['answers'].items() if start <= int(q_id) <= end]
        attempted_sec = sum(1 for a in section_answers if a['selected_option'] != 'skipped')
        correct_sec = sum(1 for a in section_answers if a['correctness'] == 'correct')
        incorrect_sec = sum(1 for a in section_answers if a['correctness'] == 'incorrect')
        skipped_sec = sum(1 for a in section_answers if a['correctness'] == 'skipped')
        accuracy = round((correct_sec / attempted_sec * 100), 2) if attempted_sec > 0 else 0
        section_stats[section] = {
            'attempted': attempted_sec,
            'correct': correct_sec,
            'incorrect': incorrect_sec,
            'skipped': skipped_sec,
            'accuracy': accuracy
        }

        topic_stats[section] = {}
        for topic_range, topic_name in data['topics'].items():
            if '-' in topic_range:
                try:
                    topic_start, topic_end = map(int, topic_range.split('-'))
                except ValueError as e:
                    print(f"Error: Failed to parse topic_range '{topic_range}' in section '{section}' for topic '{topic_name}'. Error: {e}. Skipping.")
                    continue
            else:
                try:
                    topic_start = topic_end = int(topic_range)
                except ValueError as e:
                    print(f"Error: Failed to parse topic_range '{topic_range}' in section '{section}' for topic '{topic_name}'. Error: {e}. Skipping.")
                    continue

            topic_answers = [a for q_id, a in performance['answers'].items() if topic_start <= int(q_id) <= topic_end]
            attempted_top = sum(1 for a in topic_answers if a['selected_option'] != 'skipped')
            correct_top = sum(1 for a in topic_answers if a['correctness'] == 'correct')
            incorrect_top = sum(1 for a in topic_answers if a['correctness'] == 'incorrect')
            skipped_top = sum(1 for a in topic_answers if a['correctness'] == 'skipped')
            accuracy_top = round((correct_top / attempted_top * 100), 2) if attempted_top > 0 else 0
            topic_stats[section][topic_name] = {
                'attempted': attempted_top,
                'correct': correct_top,
                'incorrect': incorrect_top,
                'skipped': skipped_top,
                'accuracy': accuracy_top
            }

    return section_stats, topic_stats

def save_to_excel(student_data, performance, output_dir='reports'):
    # Extract student data
    student_name = student_data.get('name', 'Unknown')
    student_number = student_data.get('student_id', 'Unknown')
    correct = performance['summary']['correct']
    total_questions = performance['summary']['total_questions']
    percentage = round((correct / total_questions * 100), 2)

    # Define Excel file path
    excel_path = os.path.join(output_dir, 'student_scores.xlsx')

    # Prepare data for Excel
    new_data = {
        'Name': [student_name],
        'Number': [student_number],
        'Correct': [correct],
        'Total': [total_questions],
        'Percentage': [percentage]
    }
    new_df = pd.DataFrame(new_data)

    # Check if Excel file exists
    if os.path.exists(excel_path):
        # Load existing data
        existing_df = pd.read_excel(excel_path)
        # Check if student already exists (based on Number)
        if student_number not in existing_df['Number'].values:
            # Append new data
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            # Update existing student's data
            existing_df.loc[existing_df['Number'] == student_number, ['Name', 'Correct', 'Total', 'Percentage']] = [
                student_name, correct, total_questions, percentage
            ]
            updated_df = existing_df
    else:
        # Create new Excel file
        updated_df = new_df

    # Save to Excel
    updated_df.to_excel(excel_path, index=False)
    print(f"Saved/Updated student data to {excel_path}")

def get_student_rank(student_data, output_dir='reports'):
    student_number = student_data.get('student_id', 'Unknown')
    excel_path = os.path.join(output_dir, 'student_scores.xlsx')

    if not os.path.exists(excel_path):
        return None  # No ranking if Excel file doesn't exist yet

    # Load Excel data
    df = pd.read_excel(excel_path)
    # Sort by Percentage in descending order
    df_sorted = df.sort_values(by='Percentage', ascending=False).reset_index(drop=True)
    # Find the rank of the current student
    rank = df_sorted.index[df_sorted['Number'] == student_number].tolist()
    if not rank:
        return None  # Student not found in Excel
    rank = rank[0] + 1  # Convert to 1-based ranking

    # Cap rank at 100
    total_students = len(df_sorted)
    if total_students > 100:
        if rank > 100:
            return None  # Rank not displayed if beyond 100
        total_students = 100

    return {'rank': rank, 'total': total_students}

def load_json_data(file_path, default_data=None):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_data if default_data is not None else {}
    print(questions)
def generate_html_report(student_data, questions, metadata, output_dir='reports'):
    performance = assess_performance(student_data, questions, metadata)
    section_stats, topic_stats = generate_stats(performance, metadata)
    # Save student data to Excel
    save_to_excel(student_data, performance, output_dir)

    total_questions = performance['summary']['total_questions']
    attempted = performance['summary']['attempted']
    correct = performance['summary']['correct']
    incorrect = performance['summary']['incorrect']
    skipped = performance['summary']['skipped']
    percentage = round((correct / total_questions * 100), 2)

    student_name = student_data.get('name', 'Student')

    weak_areas = []
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['skipped'] >= 2 or stats['incorrect'] > stats['correct'] or stats['accuracy'] < 50:
                weak_areas.append((section, topic, stats))

    strength_areas = []
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['attempted'] > 0 and stats['accuracy'] > 80:
                strength_areas.append((section, topic, stats))

    # Load tips from JSON
    # Load tips from JSON
    tips_data = load_json_data(os.path.join('config', 'tips.json'), {
        "score_ranges": [
            {"min": 0, "max": 40,
             "tips": ["Focus on daily practice across all sections.", "Review basic concepts to improve your score."],
             "category": "critical"},
            {"min": 40, "max": 70,
             "tips": ["Target weak areas with focused practice.", "Increase attempt rate to boost your percentage."],
             "category": "moderate"},
            {"min": 70, "max": 100,
             "tips": ["Keep refining your skills for perfection.", "Maintain your momentum with regular revision."],
             "category": "maintenance"}
        ],
        "skipped_threshold": 30,
        "skipped_tips": ["Practice mock tests to improve pacing.", "Avoid skipping questions to maximize attempts."],
        "skipped_category": "moderate",
        "section_tips": {
            "Mathematics": {"low_accuracy": "Solve 15 daily problems to improve accuracy."},
            "Physics": {"low_accuracy": "Practice 10 daily numericals for better results."},
            "Chemistry": {"low_accuracy": "Use flashcards to review key concepts."},
            "English": {"low_accuracy": "Enhance skills with daily reading practice."}
        },
        "section_category": "critical"
    })
    tips = []

    # Score-based tips
    overall_accuracy = round((correct / total_questions * 100), 2)
    for range_data in tips_data['score_ranges']:
        if range_data['min'] <= overall_accuracy <= range_data['max']:
            if range_data['tips']:  # Ensure the list isn't empty
                tips.append((secrets.choice(range_data['tips']),
                             range_data.get('category', 'general')))  # Use .get with default
            break

    # Skipped questions tip
    if skipped > total_questions * (tips_data['skipped_threshold'] / 100):
        if tips_data['skipped_tips']:  # Ensure the list isn't empty
            tips.append((secrets.choice(tips_data['skipped_tips']),
                         tips_data.get('skipped_category', 'moderate')))  # Use .get with default

    # Section-based tips for weak areas
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['skipped'] >= 2 or stats['incorrect'] > stats['correct'] or stats['accuracy'] < 50:
                if section in tips_data['section_tips'] and 'low_accuracy' in tips_data['section_tips'][section]:

                    # edit tips text if needed
                    # tip_text = f"{tips_data['section_tips'][section]['low_accuracy']} (Topic: {topic}, Accuracy: {stats['accuracy']:.2f}%)"

                    tip_text = f"{tips_data['section_tips'][section]['low_accuracy']} (Topic: {topic})"
                    tips.append((tip_text, tips_data.get('section_category', 'critical')))  # Use .get with default

    # Limit to 3 unique tips (based on tip text only)
    tips = list({tip: cat for tip, cat in tips}.items())[
           :3]  # Convert to list of (tip, category) tuples, keeping first category

    tips_list = "".join(
        [f'<li class="tip-{category}">{tip}</li>' for tip, category in tips])  # Use category for styling




    # Load quotes and limit to 1-2
    quotes = load_quotes(QUOTES_PATH)
    quote_category = 'low' if overall_accuracy < 40 else 'moderate' if overall_accuracy <= 70 else 'high'
    selected_quotes = quotes[quote_category][:2]  # Take only the first 2 quotes
    # Personalize quotes with student name
    selected_quotes = [quote.replace("You're", f"{student_name}, you're") if "You're" in quote else f"{student_name}, {quote}" for quote in selected_quotes]

    report_date = REPORT_TIME

    # Data for charts
    overall_chart_data = [correct, incorrect, skipped]
    overall_chart_labels = ['Correct', 'Incorrect', 'Skipped']
    section_chart_data = [stats['accuracy'] for stats in section_stats.values()]
    section_chart_labels = list(section_stats.keys())

    # Topic-wise chart data with colors
    topic_charts = {}
    color_map = {'Physics': '#4CAF50', 'Mathematics': '#2196F3', 'Chemistry': '#F44336', 'English': '#9C27B0'}
    for section, topics in topic_stats.items():
        topic_labels = list(topics.keys())
        topic_data = [stats['accuracy'] for stats in topics.values()]
        topic_stats_list = [{'name': name, 'stats': stats} for name, stats in topics.items()]
        topic_charts[section] = {'labels': topic_labels, 'data': topic_data, 'color': color_map.get(section, '#FF9800'), 'stats': topic_stats_list}

    # Donut chart data for strengths
    strength_counts = {}
    for section, _, _ in strength_areas:
        strength_counts[section] = strength_counts.get(section, 0) + 1
    strength_series = [count for count in strength_counts.values()]
    strength_labels = [f"{section} ({count})" for section, count in strength_counts.items()]

    # Donut chart data for weak areas
    weak_counts = {}
    for section, _, _ in weak_areas:
        weak_counts[section] = weak_counts.get(section, 0) + 1
    weak_series = [count for count in weak_counts.values()]
    weak_labels = [f"{section} ({count})" for section, count in weak_counts.items()]

    # Radar chart data for strengths and weaknesses
    radar_labels = list(section_stats.keys())
    radar_strengths = [stats['accuracy'] if any((section, topic, s) in strength_areas for topic, s in topic_stats[section].items()) else 0 for section, stats in section_stats.items()]
    radar_weaknesses = [stats['accuracy'] if any((section, topic, s) in weak_areas for topic, s in topic_stats[section].items()) else 0 for section, stats in section_stats.items()]

    # Summary card data
    highest_section = max(section_stats.items(), key=lambda x: x[1]['accuracy'], default=("None", {'accuracy': 0}))
    most_critical = min(weak_areas, key=lambda x: x[2]['accuracy'], default=("None", "None", {'accuracy': 100}))

    # Personalized summary message
    summary_message = (
        f"Great job, {student_name}!" if overall_accuracy > 70 else
        f"Keep improving, {student_name}!" if overall_accuracy < 40 else
        f"Good effort, {student_name}! Let's target those weak areas."
    )

    tips_list = "".join([f'<li class="tip-{category}">{tip}</li>' for tip, category in tips])
    quotes_list = "".join([f'<p class="quote {"featured-quote" if i == 0 else ""}">{quote}</p>' for i, quote in enumerate(selected_quotes)])

    base_name = os.path.basename(json_file)
    student_id_parts = base_name.split('_')
    student_id = student_id_parts[2] if len(student_id_parts) > 2 and student_id_parts[0] == 'student' and student_id_parts[1] == 'answers' else student_data.get('student_id', 'unknown')

    # Use student name for the report filename
    student_name_clean = student_data.get('name', 'Unknown').replace(' ', '_')  # Replace spaces with underscores
    html_path = os.path.join(output_dir, f'{TEST_NAME}_Report_{student_name}.html')

    # Get student rank
    rank_info = get_student_rank(student_data, output_dir)
    rank_display = ""

    # Load badges from JSON
    badges_data = load_json_data(os.path.join('config', 'badges.json'), [])

    if rank_info:
        rank = rank_info['rank']
        total_students = rank_info['total']
        badge_text = ""
        badge_color = ""
        badge_description = ""

        # Find matching badge
        for badge in badges_data:
            if badge['min_rank'] <= rank <= badge['max_rank']:
                badge_text = badge['text'].replace('{rank}', str(rank))
                badge_color = badge['color']
                badge_description = badge['description']
                break

        if badge_text:
            rank_display = f'<div class="rank-badge" style="background-color: {badge_color}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; margin-left: 10px; display: inline-block;" title="{badge_description}">Rank: {badge_text} (out of {total_students})</div>'

    # Load instructor notes
    notes_data = load_json_data(os.path.join('config', 'instructor_notes.json'), {"notes": []})
    note_display = ""
    for note in notes_data:
        if note['student_id'] == student_data['student_id']:
            note_display = f'<p class="summary-text">{note["message"]}</p>'
            break

    has_weaknesses = len(weak_series) > 0 and sum(weak_series) > 0
    weak_content = '''
        <div class="chart-container strength-weakness-container" id="weakDonutChart"></div>
    ''' if has_weaknesses else '''
        <div class="chart-container strength-weakness-container no-weakness-message">
            <p class="no-weakness-text">Congratulations! No weaknesses identified. Keep up the excellent work!</p>
        </div>
    '''
    print(1,strength_series)
    print(2,topic_stats)
    print(3,topic_labels)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{REPORT_TITLE} - {student_id}</title>
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- ApexCharts -->
        <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
        <!-- html2canvas -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <!-- Load jsPDF explicitly -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333;
                background-color: #f0f2f5;
                padding: 20px 0;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            h1 {{
                color: #2E86C1;
                text-align: center;
                font-size: 2.5rem;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            h2 {{
                color: #444;
                font-size: 1.75rem;
                margin-bottom: 20px;
                font-weight: 500;
                text-align: center;
            }}
            h3 {{
                color: #555;
                font-size: 1.5rem;
                margin-bottom: 15px;
                font-weight: 500;
                text-align: center;
            }}
            #section-section-wise h3 {{
                margin-bottom: 30px; /* Added space between section title and graph title */
            }}
            .section {{
                margin-bottom: 80px;
                padding: 20px;
                background-color: #fff;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                page-break-inside: avoid;
            }}
            .section:hover {{
                transform: translateY(-2px);
            }}
            .summary-card {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .chart-container {{
                position: relative;
                width: 100%;
                height: 400px;
                margin: 20px 0;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .strength-weakness-container {{
                height: 350px;
                margin-bottom: 30px;
                width: 100%;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }}
            .strength-weakness-wrapper {{
                display: flex;
                flex-direction: column;
                gap: 50px;
                height: 900px;
                align-items: center;
                page-break-inside: avoid;
            }}
            .chart-container::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 40px;
                height: 40px;
                border: 4px solid #2E86C1;
                border-top: 4px solid transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                transform: translate(-50%, -50%);
            }}
            .chart-container.loaded::before {{
                display: none;
            }}
            .no-weakness-message::before {{
                display: none !important;
            }}
            .no-weakness-message {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 350px;
                text-align: center;
            }}
            .no-weakness-text {{
                font-size: 1.2rem;
                color: #388E3C;
                font-weight: 500;
            }}
            .summary-text {{
                font-size: 1.1rem;
                margin-bottom: 15px;
                color: #666;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 10px;
                font-size: 1rem;
            }}
            .tip-critical {{
                color: #D32F2F;
                font-weight: 500;
            }}
            .tip-moderate {{
                color: #F57C00;
                font-weight: 500;
            }}
            .tip-maintenance {{
                color: #388E3C;
                font-weight: 500;
            }}
            .quote {{
                font-style: italic;
                color: #555;
                margin: 10px 0;
                font-size: 0.95rem;
            }}
            .featured-quote {{
                font-size: 1.1rem;
                color: #2E86C1;
                font-weight: 500;
            }}
            .download-btn {{
                margin-bottom: 20px;
                margin-right: 20px;
                text-align: right;
            }}
            .loading-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(5px);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                color: white;
                font-size: 1.2rem;
            }}
            .progress-container {{
                width: 50%;
                background-color: #f3f3f3;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .progress-bar {{
                width: 0%;
                height: 20px;
                background-color: #2E86C1;
                border-radius: 5px;
                transition: width 0.3s ease-in-out;
            }}
            @media print {{
                body {{
                    padding: 10mm;
                }}
                .container {{
                    width: 100%;
                    max-width: 190mm; /* A4 width minus margins */
                    margin: 0 auto;
                }}
                h1 {{
                    font-size: 2.5rem;
                    margin-bottom: 10mm;
                }}
                h2 {{
                    font-size: 1.75rem;
                    margin-bottom: 10mm;
                    text-align: center;
                }}
                h3 {{
                    font-size: 1.5rem;
                }}
                #section-section-wise h3 {{
                    margin-bottom: 30px; /* Maintain space in PDF */
                }}
                .summary-text {{
                    font-size: 1.1rem;
                }}
                .section {{
                    margin-bottom: 20px;
                    padding: 15px;
                    page-break-inside: avoid;
                    break-inside: avoid;
                }}
                .strength-weakness-wrapper {{
                    height: 700px;
                    gap: 30px;
                    page-break-inside: avoid;
                    break-inside: avoid;
                }}
                .chart-container {{
                    height: 350px;
                }}
                .strength-weakness-container {{
                    height: 300px;
                    max-width: 500px;
                }}
                .no-weakness-text {{
                    font-size: 1.2rem;
                }}
                .download-btn {{
                    display: none;
                }}
                .loading-overlay {{
                    display: none;
                }}
                .apexcharts-toolbar {{
                    display: none;
                }}
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            @media (max-width: 768px) {{
                h1 {{
                    font-size: 2rem;
                }}
                h2 {{
                    font-size: 1.5rem;
                }}
                h3 {{
                    font-size: 1.25rem;
                }}
                .summary-text {{
                    font-size: 1rem;
                }}
                .chart-container {{
                    height: 300px;
                }}
                .strength-weakness-container {{
                    height: 450px;
                    max-width: 100%;
                }}
                .strength-weakness-wrapper {{
                    height: 1430px;
                }}
                .section {{
                    padding: 20px;
                    margin-bottom: 88px;
                }}
                .tips-section {{
                    margin-top: 50px !important;
                }}
                .no-weakness-text {{
                    font-size: 1rem;
                }}
            }}
            @media (max-width: 576px) {{
                h1 {{
                    font-size: 1.5rem;
                }}
                h2 {{
                    font-size: 1.2rem;
                }}
                h3 {{
                    font-size: 1rem;
                }}
                .summary-text {{
                    font-size: 0.9rem;
                }}
                .chart-container {{
                    height: 250px;
                }}
                .strength-weakness-container {{
                    height: 400px;
                    max-width: 100%;
                }}
                .strength-weakness-wrapper {{
                    height: 1300px;
                }}
                .section {{
                    margin-bottom: 77px;
                }}
                .no-weakness-text {{
                    font-size: 0.9rem;
                }}
            }}
            @media (min-width: 768px) {{
                .chart-container {{
                    height: 350px;
                }}
                .strength-weakness-wrapper {{
                    height: 1400px;
                }}
                .strength-weakness-container {{
                    height: 350px;
                }}
                .row > .col-md-4, .row > .col-lg-4 {{
                    padding: 0 10px;
                }}
            }}
            @media (min-width: 1440px) {{
                h1 {{
                    font-size: 3rem;
                }}
                h2 {{
                    font-size: 2rem;
                }}
                h3 {{
                    font-size: 1.75rem;
                }}
                .summary-text {{
                    font-size: 1.2rem;
                }}
                .chart-container {{
                    height: 300px;
                }}
                .strength-weakness-wrapper {{
                    height: 1600px;
                }}
                .strength-weakness-container {{
                    height: 400px;
                }}
                .row > .col-lg-4 {{
                    flex: 0 0 30%;
                    max-width: 30%;
                }}
            }}
            .rank-badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .tip-maintenance {{
            color: #388E3C; /* Green for maintenance */
            font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="download-btn">
            <button class="btn btn-primary" onclick="downloadPDF()">Download as PDF</button>
        </div>
        <div class="container" id="content-to-pdf">
            <h1>{REPORT_TITLE}</h1>
            <h2>{TEST_NAME} Date: {TEST_DATE} | Report Generated: {report_date}</h2>
            <p class="text-center" style="font-size: 1.2rem; color: #555; margin-top: 15px;">Hello {student_name}, here’s your personalized {TEST_NAME} Report!</p>

            <div class="section summary-card" id="section-summary">
            <h3>Quick Summary</h3>
            <p class="summary-text">{summary_message}</p>
            <p class="summary-text">Score: {correct}/{total_questions} ({percentage:.2f}%)</p>
            <p class="summary-text">Top Strength: {highest_section[0]} ({highest_section[1]['accuracy']:.2f}%)</p>
            <p class="summary-text">Critical Weak Area: {most_critical[0]} - {most_critical[1]} ({most_critical[2]['accuracy']:.2f}%)</p>
                    {rank_display}
                    {note_display}
            </div>

            <div class="section" id="section-overall">
                <h3>Overall Performance</h3>
                <p class="summary-text">Score: {correct}/{total_questions} ({percentage:.2f}%)</p>
                <p class="summary-text">Attempted: {attempted}, Skipped: {skipped}</p>
                <div class="row">
                    <div class="col-12 col-md-4 col-lg-4 mb-3">
                        <div class="chart-container" id="progressChart"></div>
                    </div>
                    <div class="col-12 col-md-4 col-lg-4 mb-3">
                        <div class="chart-container" id="overallPieChart"></div>
                    </div>
                    <div class="col-12 col-md-4 col-lg-4">
                        <div class="chart-container" id="overallBarChart"></div>
                    </div>
                </div>
            </div>

            <div class="section" id="section-section-wise">
                <h3>Section-wise Performance</h3>
                <div class="chart-container" id="sectionChart"></div>
            </div>

            <div class="section" id="section-topic-wise">
                <h3>Topic-wise Insights</h3>
                <div class="row">
                    {''.join([
        f'<div class="col-12 col-md-6 col-lg-6 mb-4"><h4>{section}</h4><div class="chart-container" id="topicChart_{section.replace(" ", "_")}"></div></div>'
        for section in topic_charts.keys()
    ])}
                </div>
            </div>

            <div class="section" id="section-strength-weakness">
                <h3>Strengths & Weaknesses</h3>
                <div class="strength-weakness-wrapper">
                    <div class="chart-container strength-weakness-container" id="strengthDonutChart"></div>
                    {weak_content}
                    <div class="chart-container strength-weakness-container" id="radarChart"></div>
                </div>
                <div style="margin-top: 50px;"></div>
            </div>

            <div class="section tips-section" id="section-tips" style="margin-top: 80px;">
                <h3>Tips for Improvement</h3>
                <ul>{tips_list}</ul>
            </div>

            <div class="section" id="section-quotes">
                <h3>Keep Going!</h3>
                {quotes_list}
            </div>
        </div>
        <div class="loading-overlay" id="loadingOverlay" style="display: none;">
            <span id="loadingMessage">Preparing PDF...</span>
            <div class="progress-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>
        </div>

        <script>
            function markChartLoaded(id) {{
                document.querySelector('#' + id).classList.add('loaded');
            }}

            // Progress Chart
            new ApexCharts(document.querySelector("#progressChart"), {{
                chart: {{
                    type: 'radialBar',
                    height: '100%'
                }},
                series: [{percentage}],
                plotOptions: {{
                    radialBar: {{
                        hollow: {{
                            size: '70%'
                        }},
                        dataLabels: {{
                            show: true,
                            name: {{
                                show: true,
                                fontSize: '22px'
                            }},
                            value: {{
                                show: true,
                                fontSize: 16,
                                formatter: function (val) {{
                                    return val + '%';
                                }}
                            }}
                        }}
                    }}
                }},
                labels: ['Score'],
                colors: ['#2E86C1'],
                title: {{
                    text: 'Overall Score',
                    align: 'center'
                }},
                responsive: [{{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 250
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('progressChart'));

            // Overall Pie Chart (Distribution)
            new ApexCharts(document.querySelector("#overallPieChart"), {{
                chart: {{
                    type: 'pie',
                    height: '100%'
                }},
                series: {json.dumps(overall_chart_data)},
                labels: {json.dumps(overall_chart_labels)},
                colors: ['#4CAF50', '#F44336', '#FF9800'],
                title: {{
                    text: 'Answer Distribution',
                    align: 'center'
                }},
                responsive: [{{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 250
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('overallPieChart'));

            // Overall Bar Chart (Performance Breakdown)
            new ApexCharts(document.querySelector("#overallBarChart"), {{
                chart: {{
                    type: 'bar',
                    height: '100%'
                }},
                series: [{{
                    name: 'Count',
                    data: {json.dumps(overall_chart_data)}
                }}],
                xaxis: {{
                    categories: {json.dumps(overall_chart_labels)},
                    title: {{
                        text: 'Categories'
                    }}
                }},
                yaxis: {{
                    max: {total_questions},
                    title: {{
                        text: 'Questions'
                    }}
                }},
                colors: ['#4CAF50', '#F44336', '#FF9800'],
                title: {{
                    text: 'Performance Breakdown',
                    align: 'center'
                }},
                responsive: [{{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 250
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('overallBarChart'));

            // Section-wise Performance Chart
            new ApexCharts(document.querySelector("#sectionChart"), {{
                chart: {{
                    type: 'bar',
                    height: '100%'
                }},
                series: [{{
                    name: 'Accuracy (%)',
                    data: {json.dumps(section_chart_data)}
                }}],
                xaxis: {{
                    categories: {json.dumps(section_chart_labels)},
                    title: {{
                        text: 'Sections'
                    }}
                }},
                yaxis: {{
                    max: 100,
                    title: {{
                        text: 'Accuracy (%)'
                    }}
                }},
                colors: ['#2196F3', '#4CAF50', '#F44336', '#9C27B0'],
                title: {{
                    text: 'Section-wise Accuracy',
                    align: 'center'
                }},
                responsive: [{{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 250
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('sectionChart'));

            // Topic-wise Charts per Section
            {''.join([
        f"""
                new ApexCharts(document.querySelector("#topicChart_{section.replace(' ', '_')}"), {{
                    chart: {{
                        type: 'bar',
                        height: '100%'
                    }},
                    series: [{{
                        name: 'Accuracy (%)',
                        data: {json.dumps(topic_charts[section]['data'])}
                    }}],
                    xaxis: {{
                        categories: {json.dumps(topic_charts[section]['labels'])},
                        title: {{
                            text: 'Topics'
                        }}
                    }},
                    yaxis: {{
                        max: 100,
                        title: {{
                            text: 'Accuracy (%)'
                        }}
                    }},
                    colors: ['{topic_charts[section]["color"]}', '#FFD700', '#90CAF9'],
                    title: {{
                        text: '{section} Topics',
                        align: 'center'
                    }},
                    dataLabels: {{
                        enabled: false
                    }},
                    tooltip: {{
                        y: {{
                            formatter: function(val, {{ series, seriesIndex, dataPointIndex }}) {{
                                const stats = {json.dumps(topic_charts[section]['stats'])}[dataPointIndex].stats;
                                return `Attempted: ${{stats.attempted}}, Correct: ${{stats.correct}}, Accuracy: ${{stats.accuracy.toFixed(2)}}%`;
                            }}
                        }}
                    }},
                    responsive: [{{
                        breakpoint: 576,
                        options: {{
                            chart: {{
                                height: 250
                            }}
                        }}
                    }}]
                }}).render().then(() => markChartLoaded('topicChart_{section.replace(" ", "_")}'));
                """
        for section in topic_charts.keys()
    ])}

            // Donut Chart for Strengths
            new ApexCharts(document.querySelector("#strengthDonutChart"), {{
                chart: {{
                    type: 'donut',
                    height: 350
                }},
                series: {json.dumps(strength_series)},
                labels: {json.dumps(strength_labels)},
                colors: ['#4CAF50', '#2196F3', '#F44336', '#9C27B0'],
                title: {{
                    text: 'Strength Distribution',
                    align: 'center'
                }},
                dataLabels: {{
                    enabled: true,
                    formatter: function (val, opts) {{
                        return opts.w.globals.labels[opts.seriesIndex];
                    }}
                }},
                tooltip: {{
                    y: {{
                        formatter: function (val) {{
                            return val + ' strong topics';
                        }}
                    }}
                }},
                responsive: [{{
                    breakpoint: 768,
                    options: {{
                        chart: {{
                            height: 450
                        }}
                    }}
                }}, {{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 400
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('strengthDonutChart'));

            // Donut Chart for Weak Areas
            {''
            if not has_weaknesses else
            '''
            new ApexCharts(document.querySelector("#weakDonutChart"), {
                chart: {
                    type: 'donut',
                    height: 350
                },
                series: ''' + json.dumps(weak_series) + ''',
                labels: ''' + json.dumps(weak_labels) + ''',
                colors: ['#F44336', '#FF9800', '#9C27B0', '#2196F3'],
                title: {
                    text: 'Weak Area Distribution',
                    align: 'center'
                },
                dataLabels: {
                    enabled: true,
                    formatter: function (val, opts) {
                        return opts.w.globals.labels[opts.seriesIndex];
                    }
                },
                tooltip: {
                    y: {
                        formatter: function (val) {
                            return val + ' weak topics';
                        }
                    }
                },
                responsive: [{
                    breakpoint: 768,
                    options: {
                        chart: {
                            height: 450
                        }
                    }
                }, {
                    breakpoint: 576,
                    options: {
                        chart: {
                            height: 400
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }]
            }).render().then(() => markChartLoaded('weakDonutChart'));
            '''
            }

            // Radar Chart for Strengths and Weaknesses
            new ApexCharts(document.querySelector("#radarChart"), {{
                chart: {{
                    type: 'radar',
                    height: 350
                }},
                series: [{{
                    name: 'Strengths',
                    data: {json.dumps(radar_strengths)}
                }}, {{
                    name: 'Weaknesses',
                    data: {json.dumps(radar_weaknesses)}
                }}],
                xaxis: {{
                    categories: {json.dumps(radar_labels)}
                }},
                yaxis: {{
                    max: 100
                }},
                colors: ['#4CAF50', '#F44336'],
                title: {{
                    text: 'Strengths vs Weaknesses',
                    align: 'center'
                }},
                responsive: [{{
                    breakpoint: 768,
                    options: {{
                        chart: {{
                            height: 450
                        }}
                    }}
                }}, {{
                    breakpoint: 576,
                    options: {{
                        chart: {{
                            height: 400
                        }}
                    }}
                }}]
            }}).render().then(() => markChartLoaded('radarChart'));

            // Download PDF Functionality with Progress Bar
            async function downloadPDF() {{
                const loadingOverlay = document.getElementById('loadingOverlay');
                const loadingMessage = document.getElementById('loadingMessage');
                const progressBar = document.getElementById('progressBar');

                // Set overlay dimensions to current viewport size
                loadingOverlay.style.display = 'flex';
                loadingMessage.textContent = 'Preparing PDF...';
                progressBar.style.width = '0%';

                const {{ jsPDF }} = window.jspdf;
                if (!jsPDF) {{
                    console.error("jsPDF is not loaded!");
                    loadingOverlay.style.display = 'none';
                    return;
                }}
                const doc = new jsPDF({{
                    orientation: 'portrait',
                    unit: 'mm',
                    format: 'a4'
                }});

                // Create temporary wrapper for large screen rendering
                const tempWrapper = document.createElement('div');
                tempWrapper.style.width = '1400px';
                tempWrapper.style.margin = '0 auto';
                document.body.appendChild(tempWrapper);

                // Capture title, subheading, and greeting
                const titleElement = document.querySelector('h1');
                const subheadingElement = document.querySelector('h2');
                const greetingElement = document.querySelector('p.text-center');
                const tempTitleDiv = document.createElement('div');
                tempTitleDiv.style.width = '100%';
                tempTitleDiv.style.textAlign = 'center';
                const clonedTitle = titleElement.cloneNode(true);
                const clonedSubheading = subheadingElement.cloneNode(true);
                const clonedGreeting = greetingElement.cloneNode(true);
                clonedSubheading.style.marginTop = '10px';
                clonedGreeting.style.marginTop = '15px';
                tempTitleDiv.appendChild(clonedTitle);
                tempTitleDiv.appendChild(clonedSubheading);
                tempTitleDiv.appendChild(clonedGreeting);
                tempWrapper.appendChild(tempTitleDiv);

                loadingMessage.textContent = 'Capturing title...';
                progressBar.style.width = '10%';
                const titleCanvas = await html2canvas(tempTitleDiv, {{
                    scale: 2,
                    useCORS: true
                }});
                const titleImgData = titleCanvas.toDataURL('image/jpeg', 0.98);
                const titleImgWidth = 190; // A4 width minus margins
                const titleImgHeight = (titleCanvas.height * titleImgWidth) / titleCanvas.width;

                let currentY = 10;
                doc.addImage(titleImgData, 'JPEG', 10, currentY, titleImgWidth, titleImgHeight);
                currentY += titleImgHeight + 10; // Add gap after title

                tempWrapper.removeChild(tempTitleDiv);
                progressBar.style.width = '20%';

                // Capture sections
                const sections = [
                    'section-summary',
                    'section-overall',
                    'section-section-wise',
                    'section-topic-wise',
                    'section-strength-weakness',
                    'section-tips',
                    'section-quotes'
                ];

                const totalSteps = sections.length + 2; // +2 for title and saving
                let currentStep = 2; // Start after title

                for (let i = 0; i < sections.length; i++) {{
                    const section = document.getElementById(sections[i]);
                    if (!section) continue;

                    loadingMessage.textContent = `Capturing ${{section.id}}...`;
                    currentStep++;
                    progressBar.style.width = `${{(currentStep / totalSteps) * 100}}%`;

                    const tempSectionDiv = document.createElement('div');
                    tempSectionDiv.style.width = '100%';
                    const clonedSection = section.cloneNode(true);
                    tempSectionDiv.appendChild(clonedSection);
                    tempWrapper.appendChild(tempSectionDiv);

                    const canvas = await html2canvas(tempSectionDiv, {{
                        scale: 2,
                        useCORS: true
                    }});

                    const imgData = canvas.toDataURL('image/jpeg', 0.98);
                    const imgWidth = 190; // A4 width minus margins
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;

                    if (currentY + imgHeight > 297 - 10) {{ // A4 height is 297mm, minus bottom margin
                        doc.addPage();
                        currentY = 10;
                    }}

                    doc.addImage(imgData, 'JPEG', 10, currentY, imgWidth, imgHeight);
                    currentY += imgHeight + 20; // Gap between sections

                    tempWrapper.removeChild(tempSectionDiv);
                }}

                document.body.removeChild(tempWrapper);
                loadingMessage.textContent = 'Saving PDF...';
                progressBar.style.width = '100%';
                doc.save(`{TEST_NAME}_Report_${student_id}.pdf`);
                loadingOverlay.style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    html_path = os.path.join(output_dir, f'{TEST_NAME}_Report_{student_name}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated HTML report for {json_file}: {html_path}")
    return html_path

# Define directories
student_data_dir = os.getenv('STUDENT_DATA_DIR', 'student_data')  # Directory for student answers
config_dir = os.getenv('CONFIG_DIR', 'config')  # Directory for config files
output_dir = os.getenv('OUTPUT_DIR', 'reports')

# Load metadata and questions
with open(os.path.join(config_dir, 'metadata_mock_test_16.json'), 'r', encoding='utf-8') as f:
    metadata = json.load(f)

with open(os.path.join(config_dir, 'questions.json'), 'r', encoding='utf-8') as f:
    questions = {str(q['id']): q for q in json.load(f)}

print(1,config_dir)
print(2,student_data_dir)
print(3,questions)
print(4,metadata)
# Process student answers files
for json_file in glob.glob(os.path.join(student_data_dir, 'student_answers_*.json')):
    with open(json_file, 'r', encoding='utf-8') as f:
        student_data = json.load(f)
    print(5,student_data)

    html_path = generate_html_report(student_data, questions, metadata, output_dir)
    print(f"Generated report for {os.path.basename(json_file)}: {html_path}")
