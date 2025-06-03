import json
import os
from PyPDF2 import PdfReader

# Load metadata
def load_metadata(metadata_path):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load questions (assuming questions.json is provided)
def load_questions(questions_path):
    with open(questions_path, 'r', encoding='utf-8') as f:
        return {q['id']: q for q in json.load(f)}

# Parse student answers and assess performance
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
                'correctness': 'correct' if student_answer == correct_answer else 'incorrect' if student_answer != 'skipped' else 'skipped'
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

# Generate topic-wise and section-wise stats
def generate_stats(performance, metadata):
    section_stats = {}
    topic_stats = {}
    for section, data in metadata['sections'].items():
        start, end = data['range']
        section_answers = [a for q_id, a in performance['answers'].items() if start <= q_id <= end]
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
                start, end = map(int, topic_range.split('-'))
            else:
                start = end = int(topic_range)
            topic_answers = [a for q_id, a in performance['answers'].items() if start <= q_id <= end]
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

# Generate report
def generate_report(student_data, questions, metadata, output_dir='reports'):
    performance = assess_performance(student_data, questions, metadata)
    section_stats, topic_stats = generate_stats(performance, metadata)

    total_questions = performance['summary']['total_questions']
    attempted = performance['summary']['attempted']
    correct = performance['summary']['correct']
    incorrect = performance['summary']['incorrect']
    skipped = performance['summary']['skipped']
    percentage = (correct / total_questions) * 100

    # Assess weak areas
    weak_areas = []
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['skipped'] >= 2 or stats['incorrect'] > stats['correct'] or stats['accuracy'] < 50:
                weak_areas.append((section, topic, stats))

    # Generate improvement tips
    tips = []
    overall_accuracy = (correct / total_questions) * 100
    if overall_accuracy < 40:
        tips.append("<li><strong>Overall Performance:</strong> Your score is below 40%. Focus on consistent daily practice across all sections.</li>")
    elif 40 <= overall_accuracy < 70:
        tips.append("<li><strong>Overall Performance:</strong> Your score is moderate (40%-70%). Target weak areas with targeted practice.</li>")
    else:
        tips.append("<li><strong>Overall Performance:</strong> Great job with over 70%! Maintain momentum and refine your skills.</li>")

    if any(area[0] == 'Mathematics' for area in weak_areas):
        tips.append("<li><strong>Mathematics:</strong> Weak in Trigonometry or Calculus? Practice 15 problems per topic daily.</li>")
    if any(area[0] == 'Physics' for area in weak_areas):
        tips.append("<li><strong>Physics:</strong> Struggling with Mechanics or Electromagnetism? Solve 10 numerical problems daily.</li>")
    if any(area[0] == 'Chemistry' for area in weak_areas):
        tips.append("<li><strong>Chemistry:</strong> Review Organic Chemistry or Acids and Bases with flashcards.</li>")
    if any(area[0] == 'English' for area in weak_areas):
        tips.append("<li><strong>English:</strong> Improve vocabulary and grammar. Read articles and practice writing daily.</li>")
    if skipped > total_questions * 0.3:
        tips.append("<li><strong>Time Management:</strong> You skipped over 30% of questions. Practice mock tests to improve pace.</li>")

    # Prepare data for charts
    overall_data = {
        'correct': correct,
        'incorrect': incorrect,
        'skipped': skipped
    }
    section_data = {section: stats['correct'] for section, stats in section_stats.items()}

    # Generate HTML content with charts
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MUET Entry Test Performance Report</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f7fa; color: #333; margin: 0; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: 0 auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
            h1, h2, h3 {{ color: #4a90e2; }}
            h1 {{ text-align: center; margin-bottom: 20px; }}
            .summary-box, .section-box, .topic-box, .weak-areas, .tips-box, .motivation {{ border: 1px solid #e0e6ed; padding: 15px; border-radius: 5px; margin-bottom: 20px; background-color: #f9fafc; }}
            .summary-box p, .section-box p, .topic-box p, .weak-areas p, .tips-box p {{ margin: 5px 0; }}
            .section-box table, .topic-box table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .section-box th, .section-box td, .topic-box th, .topic-box td {{ padding: 10px; border: 1px solid #e0e6ed; text-align: left; }}
            .section-box th, .topic-box th {{ background-color: #e0f0ff; color: #333; }}
            .tips-box ul {{ padding-left: 20px; }}
            .chart-container {{ margin-bottom: 20px; max-width: 100%; }}
            canvas {{ max-width: 100%; height: auto; }}
            .motivation {{ text-align: center; font-style: italic; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MUET Entry Test Performance Report</h1>
            <p style="text-align: center; color: #666;">Test Date: May 23, 2025 | Report Generated: May 23, 2025</p>

            <div class="summary-box">
                <h2>Overall Performance Summary</h2>
                <p><strong>Total Questions:</strong> {total_questions}</p>
                <p><strong>Attempted Questions:</strong> {attempted}</p>
                <p><strong>Correct Answers:</strong> {correct}</p>
                <p><strong>Incorrect Answers:</strong> {incorrect}</p>
                <p><strong>Skipped Questions:</strong> {skipped}</p>
                <p><strong>Score:</strong> {correct} out of {total_questions}</p>
                <p><strong>Percentage:</strong> {percentage:.2f}%</p>
                <div class="chart-container">
                    <canvas id="overallChart"></canvas>
                </div>
            </div>

            <div class="section-box">
                <h2>Section-wise Performance</h2>
                <div class="chart-container">
                    <canvas id="sectionChart"></canvas>
                </div>
                <table>
                    <tr>
                        <th>Section</th>
                        <th>Questions</th>
                        <th>Attempted</th>
                        <th>Correct</th>
                        <th>Incorrect</th>
                        <th>Skipped</th>
                        <th>Accuracy</th>
                    </tr>
                    {"".join([
                        f'<tr><td>{section} (Q{start}–{end})</td><td>{end - start + 1}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}% ({stats["correct"]}/{stats["attempted"] if stats["attempted"] > 0 else 1})</td></tr>'
                        for section, (start, end), stats in [(sec, (data["range"][0], data["range"][1]), section_stats[sec]) for sec, data in metadata['sections'].items()]
                    ])}
                </table>
            </div>

            <div class="topic-box">
                <h2>Topic-wise Performance</h2>
                {"".join([
                    f'<h3>{section}</h3><table><tr><th>Topic</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th></tr>' +
                    "".join([
                        f'<tr><td>{topic}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td></tr>'
                        for topic, stats in topic_stats.get(section, {}).items()
                    ]) + '</table>'
                    for section in metadata['sections'].keys()
                ])}
            </div>

            <div class="weak-areas">
                <h2>Weak Areas</h2>
                {"".join([
                    f'<p><strong>{section} - {topic}:</strong> Attempted: {stats["attempted"]}, Correct: {stats["correct"]}, Incorrect: {stats["incorrect"]}, Skipped: {stats["skipped"]}, Accuracy: {stats["accuracy"]:.2f}%. '
                    f'Recommendation: Focus on this topic due to {"high skipped rate" if stats["skipped"] >= 2 else "low accuracy or incorrect answers"}.</p>'
                    for section, topic, stats in weak_areas
                ]) or "<p>No significant weak areas identified. Keep up the good work!</p>"}
            </div>

            <div class="tips-box">
                <h2>Tips for Improvement</h2>
                <ul>
                    {"".join(tips) or "<li>No specific tips at this time. Continue your current study approach.</li>"}
                </ul>
            </div>

            <div class="motivation">
                <h2>Keep Going!</h2>
                <p>You've taken the first step by attempting this test—great job! With consistent practice and focus on your weak areas, you'll see improvement in no time. Keep practicing—you're on the right track!</p>
            </div>
        </div>

        <script>
            // Pie Chart for Overall Performance
            const overallCtx = document.getElementById('overallChart').getContext('2d');
            new Chart(overallCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Correct', 'Incorrect', 'Skipped'],
                    datasets: [{{
                        data: [{overall_data['correct']}, {overall_data['incorrect']}, {overall_data['skipped']}],
                        backgroundColor: ['#36a2eb', '#ff6384', '#c9cbcf'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'top' }},
                        title: {{ display: true, text: 'Overall Performance Distribution' }}
                    }}
                }}
            }});

            // Bar Chart for Section-wise Performance
            const sectionCtx = document.getElementById('sectionChart').getContext('2d');
            new Chart(sectionCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(list(section_data.keys()))},
                    datasets: [{{
                        label: 'Correct Answers',
                        data: {json.dumps(list(section_data.values()))},
                        backgroundColor: '#4a90e2',
                        borderColor: '#2b6cb0',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Number of Correct Answers' }} }},
                        x: {{ title: {{ display: true, text: 'Section' }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }},
                        title: {{ display: true, text: 'Section-wise Correct Answers' }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    # Save the report
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    student_id = os.path.basename(json_file).split('_')[2] if '_' in os.path.basename(json_file) else 'unknown'
    report_path = os.path.join(output_dir, f'MUET_Entry_Test_Report_{student_id}.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return report_path

# Main execution
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