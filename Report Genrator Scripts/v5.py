import json
import os
from datetime import datetime
from weasyprint import HTML
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from io import BytesIO
from PIL import Image
import base64

def load_metadata(metadata_path):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_questions(questions_path):
    with open(questions_path, 'r', encoding='utf-8') as f:
        return {q['id']: q for q in json.load(f)}

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
            answers[q_id] = {
                'selected_option': student_answer,
                'correctness': answer.get('correctness', 'correct' if student_answer == correct_answer else 'incorrect' if student_answer != 'skipped' else 'skipped')
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
        accuracy = (correct_sec / attempted_sec * 100) if attempted_sec > 0 else 0
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
            accuracy_top = (correct_top / attempted_top * 100) if attempted_top > 0 else 0
            topic_stats[section][topic_name] = {
                'attempted': attempted_top,
                'correct': correct_top,
                'incorrect': incorrect_top,
                'skipped': skipped_top,
                'accuracy': accuracy_top
            }

    return section_stats, topic_stats

def render_chart_to_base64(chart_type, data, labels, title, width=500, height=300, max_value=100):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x720')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #fff;
            }}
            canvas {{
                width: {width}px !important;
                height: {height}px !important;
            }}
        </style>
    </head>
    <body>
        <canvas id="chart" width="{width}" height="{height}"></canvas>
        <script>
            var ctx = document.getElementById('chart').getContext('2d');
            new Chart(ctx, {{
                type: '{chart_type}',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: '{title}',
                        data: {json.dumps(data)},
                        backgroundColor: ['#4CAF50', '#F44336', '#FF9800', '#2196F3', '#9C27B0'],
                        borderColor: ['#388E3C', '#D32F2F', '#F57C00', '#1976D2', '#7B1FA2'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: {max_value},
                            title: {{
                                display: true,
                                text: '{ "Questions" if chart_type == "bar" and title == "Performance Breakdown" else "Accuracy (%)" }'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Categories'
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: '{title}',
                            font: {{
                                size: 16
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    with open('temp_chart.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    driver.get('file:///' + os.path.abspath('temp_chart.html').replace('\\', '/'))
    time.sleep(20)  # Already increased to 20 seconds
    chart_base64 = driver.get_screenshot_as_base64()
    print(f"Base64 length for {title} chart: {len(chart_base64)}")
    driver.quit()
    os.remove('temp_chart.html')
    return chart_base64

def validate_and_save_image(base64_string, filename):
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        image.verify()
        absolute_path = os.path.abspath(filename)
        with open(absolute_path, 'wb') as f:
            f.write(image_data)
        print(f"Successfully saved image to {absolute_path}")
        return absolute_path, base64_string  # Return both path and base64 for fallback
    except Exception as e:
        print(f"Invalid base64 for {filename}: {e}. Using placeholder image.")
        placeholder = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAFAgECNAvMBQAAAABJRU5ErkJggg==")
        absolute_path = os.path.abspath(filename)
        with open(absolute_path, 'wb') as f:
            f.write(placeholder)
        return absolute_path, base64.b64encode(placeholder).decode('utf-8')

def generate_report(student_data, questions, metadata, output_dir='reports'):
    performance = assess_performance(student_data, questions, metadata)
    section_stats, topic_stats = generate_stats(performance, metadata)

    total_questions = performance['summary']['total_questions']
    attempted = performance['summary']['attempted']
    correct = performance['summary']['correct']
    incorrect = performance['summary']['incorrect']
    skipped = performance['summary']['skipped']
    percentage = (correct / total_questions) * 100

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

    tips = []
    overall_accuracy = (correct / total_questions) * 100
    if overall_accuracy < 40:
        tips.append("Overall Performance: Your score is below 40%. Focus on consistent daily practice across all sections.")
    elif 40 <= overall_accuracy <= 70:
        tips.append("Overall Performance: Your score is moderate (40%-70%). Target weak areas with targeted practice.")
    else:
        tips.append("Overall Performance: Excellent work with over 70%! Maintain momentum and refine skills.")

    if any(area[0] == 'Mathematics' for area in weak_areas):
        tips.append("Mathematics: Practice 15 problems daily on weak topics like Trigonometry or Calculus.")
    if any(area[0] == 'Physics' for area in weak_areas):
        tips.append("Physics: Solve 10 numerical problems daily on Mechanics or Electromagnetism.")
    if any(area[0] == 'Chemistry' for area in weak_areas):
        tips.append("Chemistry: Review Organic Chemistry or Acids and Bases with flashcards.")
    if any(area[0] == 'English' for area in weak_areas):
        tips.append("English: Improve vocabulary and grammar with daily reading and writing.")
    if skipped > total_questions * 0.3:
        tips.append("Time Management: You skipped over 30% of questions. Practice mock tests to improve pace.")

    quotes = [
        "Success is the sum of small efforts, repeated day in and day out. - Robert Collier",
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Believe you can and you're halfway there. - Theodore Roosevelt"
    ]
    quote = quotes[hash(student_data.get('student_id', 'default')) % len(quotes)]

    # Generate Overall Performance Chart
    overall_chart_data = [correct, incorrect, skipped]
    overall_chart_labels = ['Correct', 'Incorrect', 'Skipped']
    overall_chart_base64 = render_chart_to_base64('bar', overall_chart_data, overall_chart_labels, 'Performance Breakdown', width=500, height=300, max_value=total_questions)
    overall_chart_file, overall_base64 = validate_and_save_image(overall_chart_base64, "temp_overall_chart.png")

    # Generate Section-wise Performance Chart
    section_chart_data = [stats['accuracy'] for stats in section_stats.values()]
    section_chart_labels = list(section_stats.keys())
    section_chart_base64 = render_chart_to_base64('bar', section_chart_data, section_chart_labels, 'Section-wise Accuracy', width=500, height=300, max_value=100)
    section_chart_file, section_base64 = validate_and_save_image(section_chart_base64, "temp_section_chart.png")

    report_date = datetime.now().strftime('%I:%M %p PKT on %B %d, %Y')

    section_labels = json.dumps(list(section_stats.keys()))
    section_data = json.dumps([stats['accuracy'] for stats in section_stats.values()])
    section_table = "".join([
        f'<tr><td>{section} (Q{start}–{end})</td><td>{end - start + 1}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td></tr>'
        for section, (start, end), stats in
        [(sec, (data["range"][0], data["range"][1]), section_stats[sec]) for sec, data in metadata['sections'].items()]
    ])
    topic_tables = "".join([
        f'<h4>{section}</h4><table><tr><th>Topic</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th></tr>' +
        "".join([
            f'<tr><td>{topic}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td></tr>'
            for topic, stats in topic_stats.get(section, {}).items()
        ]) + '</table>'
        for section in metadata['sections'].keys()
    ])
    weak_table = "".join([
        f'<tr><td>{section}</td><td>{topic}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td><td>' +
        (
            'Critical: Accuracy < 20% or high skips. Practice 20 problems daily on ' + topic.lower() + ' using Khan Academy or textbooks.' if
            stats["accuracy"] < 20 or stats["skipped"] >= 2 else
            'Moderate: Accuracy 20%-50%. Solve 10 problems daily and review concepts.' if 20 <= stats["accuracy"] <= 50 else
            'Mild: Accuracy 50%-80%. Focus on 5 problems daily to solidify skills.'
        ) + '</td></tr>'
        for section, topic, stats in weak_areas
    ]) or '<tr><td colspan="8">No significant weak areas identified. Keep up the good work!</td></tr>'
    strength_table = "".join([
        f'<tr><td>{section}</td><td>{topic}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td><td>Excellent performance! Maintain by practicing 5 problems weekly.</td></tr>'
        for section, topic, stats in strength_areas
    ]) or '<tr><td colspan="8">No standout strengths yet. Aim for consistency!</td></tr>'
    tips_list = "".join([f'<li>{tip}</li>' for tip in tips]) or '<li>No specific tips at this time. Continue your current study approach.</li>'

    base_name = os.path.basename(json_file)
    student_id_parts = base_name.split('_')
    student_id = student_id_parts[2] if len(student_id_parts) > 2 and student_id_parts[0] == 'student' and student_id_parts[1] == 'answers' else student_data.get('student_id', 'unknown')

    # Fallback: Use data URI if file path fails
    overall_chart_src = f"data:image/png;base64,{overall_base64}" if overall_base64 else overall_chart_file
    section_chart_src = f"data:image/png;base64,{section_base64}" if section_base64 else section_chart_file

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MUET Entry Test Report - {student_id}</title>
        <style>
            @page {{
                size: A4;
                margin: 0.5in;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                color: #333;
                width: 190mm;
                box-sizing: border-box;
                padding: 10mm;
            }}
            h1 {{
                color: #2E86C1;
                text-align: center;
                font-size: 24pt;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #444;
                font-size: 18pt;
                margin-bottom: 10px;
            }}
            h3 {{
                color: #666;
                font-size: 14pt;
                margin-bottom: 8px;
            }}
            h4 {{
                color: #666;
                font-size: 12pt;
                margin-bottom: 6px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 10pt;
                table-layout: fixed;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                word-wrap: break-word;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            .chart-container {{
                text-align: center;
                margin: 15px 0;
                width: 100%;
                max-width: 170mm;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
            }}
            .section {{
                margin-bottom: 20px;
                page-break-inside: avoid;
            }}
            ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>MUET Entry Test Performance Report</h1>
        <h2>Test Date: May 24, 2025 | Report Generated: {report_date}</h2>
        <div class="section">
            <h3>Overall Performance Summary</h3>
            <table>
                <tr><th>Total Questions</th><td>{total_questions}</td></tr>
                <tr><th>Attempted Questions</th><td>{attempted}</td></tr>
                <tr><th>Correct Answers</th><td>{correct}</td></tr>
                <tr><th>Incorrect Answers</th><td>{incorrect}</td></tr>
                <tr><th>Skipped Questions</th><td>{skipped}</td></tr>
                <tr><th>Score</th><td>{correct} out of {total_questions}</td></tr>
                <tr><th>Percentage</th><td>{percentage:.2f}%</td></tr>
            </table>
            <div class="chart-container">
                <img src="{overall_chart_src}" alt="Overall Performance Chart">
            </div>
        </div>
        <div class="section">
            <h3>Section-wise Performance</h3>
            <table>
                <tr><th>Section</th><th>Questions</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th></tr>
                {section_table}
            </table>
            <div class="chart-container">
                <img src="{section_chart_src}" alt="Section-wise Performance Chart">
            </div>
        </div>
        <div class="section">
            <h3>Topic-wise Performance</h3>
            {topic_tables}
        </div>
        <div class="section">
            <h3>Weak Areas</h3>
            <table>
                <tr><th>Section</th><th>Topic</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th><th>Recommendation</th></tr>
                {weak_table}
            </table>
        </div>
        <div class="section">
            <h3>Strengths</h3>
            <table>
                <tr><th>Section</th><th>Topic</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th><th>Insight</th></tr>
                {strength_table}
            </table>
        </div>
        <div class="section">
            <h3>Tips for Improvement</h3>
            <ul>{tips_list}</ul>
        </div>
        <div class="section">
            <h3>Keep Going!</h3>
            <p>{quote}</p>
        </div>
    </body>
    </html>
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    html_path = os.path.join(output_dir, f'MUET_Entry_Test_Report_{student_id}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    try:
        pdf_path = os.path.join(output_dir, f'MUET_Entry_Test_Report_{student_id}.pdf')
        print(f"Converting HTML to PDF for student {student_id} at {datetime.now().strftime('%H:%M:%S')} using WeasyPrint...")
        HTML(html_path).write_pdf(pdf_path)
        print(f"Generated PDF report for {json_file}: {pdf_path}")
    except Exception as e:
        print(f"WeasyPrint conversion failed: {e}. HTML generated at: {html_path}. Convert manually using a browser (e.g., Chrome Print to PDF).")
        return html_path
    finally:
        # Move file deletion outside the block to ensure PDF is fully written
        pass

    # Delete temporary files after PDF is confirmed written
    if os.path.exists(overall_chart_file):
        os.remove(overall_chart_file)
    if os.path.exists(section_chart_file):
        os.remove(section_chart_file)
    if os.path.exists(html_path):
        os.remove(html_path)
    return pdf_path

metadata_path = 'metadata_mock_test_16.json'
questions_path = 'questions.json'
metadata = load_metadata(metadata_path)
questions = load_questions(questions_path)

json_files = [f for f in os.listdir('.') if f.endswith('.json') and f != metadata_path and f != questions_path]

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        student_data = json.load(f)
    report_path = generate_report(student_data, questions, metadata)
    print(f"Generated report for {json_file}: {report_path}")