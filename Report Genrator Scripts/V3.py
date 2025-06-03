import json
import os
from PyPDF2 import PdfReader

# Load and parse test PDF
def parse_test_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    sections = {}
    current_section = None
    question_count = {}
    topic_mapping = {}
    cumulative_questions = 0

    for page_num in range(len(reader.pages)):
        text = reader.pages[page_num].extract_text()
        lines = text.split('\n')
        for line in lines:
            if any(section in line for section in ['Physics', 'Mathematics', 'Chemistry', 'English']):
                current_section = line.split('(')[0].strip()
                num_questions_part = line.split('(')[1].split(')')[0]
                num_questions = int(num_questions_part.replace('Questions', '').strip())
                start = cumulative_questions + 1
                end = cumulative_questions + num_questions
                sections[current_section] = (start, end)
                cumulative_questions += num_questions
                question_count[current_section] = 0
                # Initialize topic mapping with dynamic ranges based on question count
                for i in range(start, end + 1, 5):
                    topic_range = (i, min(i + 4, end))
                    topic = f"Topic_{topic_range[0]}-{topic_range[1]}"
                    topic_mapping.setdefault(current_section, {})[topic_range] = topic
            elif line.strip().startswith(str(page_num + 1) + '.') and '.' in line.split('.')[1]:
                question_id = int(line.split('.')[0])
                if current_section and (start <= question_id <= end):
                    question_count[current_section] += 1

    return sections, topic_mapping, question_count

# Generate report for a single student
def generate_report(student_data, sections, topic_mapping, output_dir='reports'):
    total_questions = student_data['summary']['total_questions']
    attempted = student_data['summary']['attempted']
    correct = student_data['summary']['correct']
    incorrect = student_data['summary']['incorrect']
    skipped = student_data['summary']['skipped']
    percentage = (correct / total_questions) * 100

    section_stats = {}
    topic_stats = {}
    for section, (start, end) in sections.items():
        section_answers = [ans for ans in student_data['answers'] if start <= ans['id'] <= end]
        attempted_sec = sum(1 for ans in section_answers if ans['selected_option'] != 'skipped')
        correct_sec = sum(1 for ans in section_answers if ans['correctness'] == 'correct')
        incorrect_sec = sum(1 for ans in section_answers if ans['correctness'] == 'incorrect')
        skipped_sec = sum(1 for ans in section_answers if ans['correctness'] == 'skipped')
        accuracy = (correct_sec / attempted_sec * 100) if attempted_sec > 0 else 0
        section_stats[section] = {
            'attempted': attempted_sec,
            'correct': correct_sec,
            'incorrect': incorrect_sec,
            'skipped': skipped_sec,
            'accuracy': accuracy
        }

        topic_stats[section] = {}
        for (t_start, t_end), topic in topic_mapping.get(section, {}).items():
            topic_answers = [ans for ans in section_answers if t_start <= ans['id'] <= t_end]
            attempted_top = sum(1 for ans in topic_answers if ans['selected_option'] != 'skipped')
            correct_top = sum(1 for ans in topic_answers if ans['correctness'] == 'correct')
            incorrect_top = sum(1 for ans in topic_answers if ans['correctness'] == 'incorrect')
            skipped_top = sum(1 for ans in topic_answers if ans['correctness'] == 'skipped')
            accuracy_top = (correct_top / attempted_top * 100) if attempted_top > 0 else 0
            topic_stats[section][topic] = {
                'attempted': attempted_top,
                'correct': correct_top,
                'incorrect': incorrect_top,
                'skipped': skipped_top,
                'accuracy': accuracy_top
            }

    # Assess weak areas
    weak_areas = []
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['skipped'] >= 2 or stats['incorrect'] > stats['correct'] or stats['accuracy'] < 50:
                weak_areas.append((section, topic, stats))

    # Generate improvement tips based on overall performance and weak areas
    tips = []
    overall_accuracy = (correct / total_questions) * 100
    if overall_accuracy < 40:
        tips.append("<li><strong>Overall Performance:</strong> Your score is below 40%. Focus on consistent daily practice across all sections.</li>")
    elif 40 <= overall_accuracy < 70:
        tips.append("<li><strong>Overall Performance:</strong> Your score is moderate (40%-70%). Target weak areas with targeted practice.</li>")
    else:
        tips.append("<li><strong>Overall Performance:</strong> Great job with over 70%! Maintain momentum and refine your skills.</li>")

    if any(area[0] == 'Physics' for area in weak_areas):
        tips.append("<li><strong>Physics:</strong> Struggling with topics like Mechanics or Electricity? Solve 10 numerical problems daily.</li>")
    if any(area[0] == 'Mathematics' for area in weak_areas):
        tips.append("<li><strong>Mathematics:</strong> Weak in Trigonometry or Calculus? Practice 15 problems per topic daily.</li>")
    if any(area[0] == 'Chemistry' for area in weak_areas):
        tips.append("<li><strong>Chemistry:</strong> Review Organic Chemistry or Reactions with flashcards and lab simulations.</li>")
    if any(area[0] == 'English' for area in weak_areas):
        tips.append("<li><strong>English:</strong> Improve vocabulary and grammar. Read articles and practice writing daily.</li>")
    if skipped > total_questions * 0.3:
        tips.append("<li><strong>Time Management:</strong> You skipped over 30% of questions. Practice mock tests to improve pace.</li>")

    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MUET Entry Test Performance Report</title>
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
            <p style="text-align: center; color: #666;">Test Date: April 11, 2025 | Report Generated: May 23, 2025</p>

            <div class="summary-box">
                <h2>Overall Performance Summary</h2>
                <p><strong>Total Questions:</strong> {total_questions}</p>
                <p><strong>Attempted Questions:</strong> {attempted}</p>
                <p><strong>Correct Answers:</strong> {correct}</p>
                <p><strong>Incorrect Answers:</strong> {incorrect}</p>
                <p><strong>Skipped Questions:</strong> {skipped}</p>
                <p><strong>Score:</strong> {correct} out of {total_questions}</p>
                <p><strong>Percentage:</strong> {percentage:.2f}%</p>
            </div>

            <div class="section-box">
                <h2>Section-wise Performance</h2>
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
                        for section, (start, end), stats in [(sec, rng, section_stats[sec]) for sec, rng in sections.items()]
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
                    for section in sections.keys()
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

            <div class="infographics">
                <h2>Performance Visualizations</h2>
                <div class="chart-container">
                    <h3>Bar Chart: Section-wise Accuracy</h3>
                    <canvas id="sectionAccuracyChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Pie Chart: Correct/Incorrect/Skipped Distribution</h3>
                    <canvas id="performanceDistributionChart"></canvas>
                </div>
                {"".join([
                    f'<div class="chart-container"><h3>Bar Chart: {section} Topic-wise Accuracy</h3><canvas id="topicAccuracyChart_{section.lower()}"></canvas></div>'
                    for section in sections.keys()
                ])}
            </div>

            <div class="motivation">
                <h2>Keep Going!</h2>
                <p>You've taken the first step by attempting this test—great job! With consistent practice and focus on your weak areas, you'll see improvement in no time. Keep practicing—you're on the right track!</p>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <script>
            const sectionAccuracyCtx = document.getElementById('sectionAccuracyChart').getContext('2d');
            new Chart(sectionAccuracyCtx, {{
                type: 'bar',
                data: {{
                    labels: [{", ".join([f'"{s}"' for s in sections.keys()])}],
                    datasets: [{{
                        label: 'Accuracy (%)',
                        data: [{", ".join([f'{stats["accuracy"]}' for stats in section_stats.values()])}],
                        backgroundColor: ["#4a90e2", "#ff6b6b", "#4ecdc4", "#ffcc5c"],
                        borderColor: ["#2a70c2", "#df4b4b", "#2eadb4", "#dfab3c"],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    scales: {{ y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Accuracy (%)' }} }}, x: {{ title: {{ display: true, text: 'Section' }} }} }},
                    plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Section-wise Accuracy (%)' }} }}
                }}
            }});

            const performanceDistributionCtx = document.getElementById('performanceDistributionChart').getContext('2d');
            new Chart(performanceDistributionCtx, {{
                type: 'pie',
                data: {{
                    labels: ["Correct", "Incorrect", "Skipped"],
                    datasets: [{{
                        data: [{correct}, {incorrect}, {skipped}],
                        backgroundColor: ["#4a90e2", "#ff6b6b", "#e0e6ed"],
                        borderColor: ["#2a70c2", "#df4b4b", "#c0c6cd"],
                        borderWidth: 1
                    }}]
                }},
                options: {{ plugins: {{ legend: {{ position: 'right' }}, title: {{ display: true, text: 'Performance Distribution' }} }} }}
            }});

            {"".join([
                f'const topicAccuracyCtx_{section.lower()} = document.getElementById("topicAccuracyChart_{section.lower()}").getContext("2d");'
                f'new Chart(topicAccuracyCtx_{section.lower()}, {{'
                f'type: "bar",'
                f'data: {{'
                f'labels: [{", ".join([f'"{topic}"' for topic in topic_stats.get(section, {}).keys()])}],'
                f'datasets: [{{'
                f'label: "Accuracy (%)",'
                f'data: [{", ".join([f"{stats['accuracy']}" for stats in topic_stats.get(section, {}).values()])}],'
                f'backgroundColor: ["#4a90e2", "#ff6b6b", "#4ecdc4", "#ffcc5c", "#8e6e95"],'
                f'borderColor: ["#2a70c2", "#df4b4b", "#2eadb4", "#dfab3c", "#6e4e75"],'
                f'borderWidth: 1'
                f'}}]'
                f'}},'
                f'options: {{'
                f'scales: {{'
                f'y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: "Accuracy (%)" }} }},'
                f'x: {{ title: {{ display: true, text: "Topic" }} }}'
                f'}},'
                f'plugins: {{'
                f'legend: {{ display: false }},'
                f'title: {{ display: true, text: "{section} Topic-wise Accuracy (%)" }}'
                f'}}'
                f'}}'
                f'}});'
                for section in sections.keys()
            ])}
        </script>
    </body>
    </html>
    """

    # Save the report
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    student_id = os.path.basename(json_file).split('_')[2] if '_' in os.path.basename(json_file) else 'unknown'
    report_path = os.path.join(output_dir, f'MUET_Entry_Test_Report_{student_id}.html')
    with open(report_path, 'w') as f:
        f.write(html_content)
    return report_path

# Main execution for multiple students
pdf_path = 'Mock_Test 09.pdf'
json_files = [f for f in os.listdir('..') if f.endswith('.json')]

sections, topic_mapping, _ = parse_test_pdf(pdf_path)

for json_file in json_files:
    with open(json_file, 'r') as f:
        student_data = json.load(f)
    report_path = generate_report(student_data, sections, topic_mapping)
    print(f"Generated report for {json_file}: {report_path}")