import json
import os

# Load JSON data
with open('../archive/dummy_student_answers_20250523_0131.json', 'r') as f:
    data = json.load(f)

# Analyze data
total_questions = data['summary']['total_questions']
attempted = data['summary']['attempted']
correct = data['summary']['correct']
incorrect = data['summary']['incorrect']
skipped = data['summary']['skipped']
percentage = (correct / total_questions) * 100

# Section-wise breakdown and topic mapping
sections = {
    'Physics': (1, 25),
    'Mathematics': (26, 50),
    'Chemistry': (51, 75),
    'English': (76, 100)
}

# Map questions to topics (based on Mock_Test_09.pdf)
topic_mapping = {
    'Physics': {
        (1, 5): 'Electricity',  # Q1: SI unit of electric current
        (6, 10): 'Mechanics',  # Q6: One horsepower, Q8: Constant velocity
        (11, 15): 'Optics',    # Q11: Refractive index
        (16, 20): 'Gravitation',  # Q16: Gravitational force
        (21, 25): 'Waves'      # Q21: Hooke's law
    },
    'Mathematics': {
        (26, 30): 'Algebra',   # Q29: f(x)=x/(x^2-4)
        (31, 35): 'Trigonometry',  # Q31: sin(α+β)
        (36, 40): 'Calculus',  # Q36: Integral of 2x dx
        (41, 45): 'Geometry',  # Q41: Area of a circle
        (46, 50): 'Coordinate Geometry'  # Q49: Distance between points
    },
    'Chemistry': {
        (51, 55): 'Organic Chemistry',  # Q51: General formula for alkanes
        (56, 60): 'Physical Chemistry',  # Q56: One mole
        (61, 65): 'Inorganic Chemistry',  # Q61: Formula of sulfuric acid
        (66, 70): 'Chemical Reactions',  # Q68: 2H₂+O₂→2H₂O
        (71, 75): 'Biochemistry'  # Q74: Formula of glucose
    },
    'English': {
        (76, 80): 'Grammar',  # Q76: Correct sentence
        (81, 85): 'Vocabulary',  # Q84: Meaning of "familiar"
        (86, 90): 'Comprehension',  # Q89: He said, "Would that I were rich."
        (91, 95): 'Sentence Correction',  # Q91: He said to his servant
        (96, 100): 'Synonyms/Antonyms'  # Q98: Synonym of "persist"
    }
}

# Analyze section-wise and topic-wise performance
section_stats = {}
topic_stats = {}
for section, (start, end) in sections.items():
    section_answers = [ans for ans in data['answers'] if start <= ans['id'] <= end]
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

    # Topic-wise stats for this section
    topic_stats[section] = {}
    for (t_start, t_end), topic in topic_mapping[section].items():
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

# Identify weak areas (topics with high incorrect or skipped rates)
weak_areas = []
for section, topics in topic_stats.items():
    for topic, stats in topics.items():
        if stats['skipped'] >= 4 or stats['incorrect'] > 0:  # Threshold: 4+ skipped or any incorrect
            weak_areas.append((section, topic, stats))

# Generate tailored tips based on weak areas
tips = []
if any(area[0] == 'Physics' for area in weak_areas):
    tips.append("<li><strong>Physics:</strong> Focus on topics like Electricity (e.g., SI units: Ampere) and Mechanics (e.g., torque, Hooke's law). Practice numerical problems daily.</li>")
if any(area[0] == 'Mathematics' for area in weak_areas):
    tips.append("<li><strong>Mathematics:</strong> Strengthen Trigonometry (e.g., \(\sin(\alpha+\beta)\)) and Calculus (e.g., integrals). Solve at least 10 problems per topic daily.</li>")
if any(area[0] == 'Chemistry' for area in weak_areas):
    tips.append("<li><strong>Chemistry:</strong> Review Organic Chemistry (e.g., alkanes: \(\mathrm{C}_n\mathrm{H}_{2n+2}\)) and Chemical Reactions (e.g., combination reactions). Use flashcards for formulas.</li>")
if any(area[0] == 'English' for area in weak_areas):
    tips.append("<li><strong>English:</strong> Since MUET emphasizes English, improve vocabulary (e.g., synonyms like 'persist') and grammar. Read English newspapers (e.g., Dawn) daily.</li>")
tips.append("<li><strong>Time Management:</strong> Practice full-length mock tests to reduce skipped questions. Aim to attempt at least 50% of the questions in your next test.</li>")

# Generate HTML report
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MUET Entry Test Performance Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f7fa;
            color: #333;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        h1, h2, h3 {{
            color: #4a90e2;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .summary-box, .section-box, .topic-box, .weak-areas, .tips-box, .motivation {{
            border: 1px solid #e0e6ed;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            background-color: #f9fafc;
        }}
        .summary-box p, .section-box p, .topic-box p, .weak-areas p, .tips-box p {{
            margin: 5px 0;
        }}
        .section-box table, .topic-box table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .section-box th, .section-box td, .topic-box th, .topic-box td {{
            padding: 10px;
            border: 1px solid #e0e6ed;
            text-align: left;
        }}
        .section-box th, .topic-box th {{
            background-color: #e0f0ff;
            color: #333;
        }}
        .tips-box ul {{
            padding-left: 20px;
        }}
        .chart-container {{
            margin-bottom: 20px;
            max-width: 100%;
        }}
        canvas {{
            max-width: 100%;
            height: auto;
        }}
        .motivation {{
            text-align: center;
            font-style: italic;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MUET Entry Test Performance Report</h1>
        <p style="text-align: center; color: #666;">Test Date: April 11, 2025 | Report Generated: May 23, 2025</p>

        <!-- Overall Performance Summary -->
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

        <!-- Section-wise Performance Breakdown -->
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
                    f'<tr><td>{section} (Q{start}–{end})</td><td>25</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}% ({stats["correct"]}/{stats["attempted"]})</td></tr>'
                    for section, (start, end), stats in [(sec, rng, section_stats[sec]) for sec, rng in sections.items()]
                ])}
            </table>
        </div>

        <!-- Topic-wise Performance Breakdown -->
        <div class="topic-box">
            <h2>Topic-wise Performance</h2>
            {"".join([
                f'<h3>{section}</h3><table><tr><th>Topic</th><th>Attempted</th><th>Correct</th><th>Incorrect</th><th>Skipped</th><th>Accuracy</th></tr>' +
                "".join([
                    f'<tr><td>{topic}</td><td>{stats["attempted"]}</td><td>{stats["correct"]}</td><td>{stats["incorrect"]}</td><td>{stats["skipped"]}</td><td>{stats["accuracy"]:.2f}%</td></tr>'
                    for topic, stats in topic_stats[section].items()
                ]) + '</table>'
                for section in sections.keys()
            ])}
        </div>

        <!-- Identification of Weak Areas -->
        <div class="weak-areas">
            <h2>Weak Areas</h2>
            {"".join([
                f'<p><strong>{section} - {topic}:</strong> Attempted: {stats["attempted"]}, Correct: {stats["correct"]}, Incorrect: {stats["incorrect"]}, Skipped: {stats["skipped"]}. '
                f'This topic needs attention due to {"high skipped rate" if stats["skipped"] >= 4 else "incorrect answers"}.</p>'
                for section, topic, stats in weak_areas
            ])}
        </div>

        <!-- Actionable Tips for Improvement -->
        <div class="tips-box">
            <h2>Tips for Improvement</h2>
            <ul>
                {"".join(tips)}
            </ul>
        </div>

        <!-- Infographics: Charts -->
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

        <!-- Motivational Closing Note -->
        <div class="motivation">
            <h2>Keep Going!</h2>
            <p>You've taken the first step by attempting this test—great job! With consistent practice and focus on your weak areas, you'll see improvement in no time. Keep practicing—you're on the right track!</p>
        </div>
    </div>

    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Bar Chart: Section-wise Accuracy
        const sectionAccuracyCtx = document.getElementById('sectionAccuracyChart').getContext('2d');
        new Chart(sectionAccuracyCtx, {{
            type: 'bar',
            data: {{
                labels: ["Physics", "Mathematics", "Chemistry", "English"],
                datasets: [{{
                    label: 'Accuracy (%)',
                    data: [{", ".join([f'{stats["accuracy"]}' for stats in section_stats.values()])}],
                    backgroundColor: ["#4a90e2", "#ff6b6b", "#4ecdc4", "#ffcc5c"],
                    borderColor: ["#2a70c2", "#df4b4b", "#2eadb4", "#dfab3c"],
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Accuracy (%)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Section'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'Section-wise Accuracy (%)'
                    }}
                }}
            }}
        }});

        // Pie Chart: Correct/Incorrect/Skipped Distribution
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
            options: {{
                plugins: {{
                    legend: {{
                        position: 'right'
                    }},
                    title: {{
                        display: true,
                        text: 'Performance Distribution'
                    }}
                }}
            }}
        }});

        // Topic-wise Accuracy Charts
        {"".join([
            f'const topicAccuracyCtx_{section.lower()} = document.getElementById("topicAccuracyChart_{section.lower()}").getContext("2d");'
            f'new Chart(topicAccuracyCtx_{section.lower()}, {{'
            f'type: "bar",'
            f'data: {{'
            f'labels: [{", ".join([f'"{topic}"' for topic in topic_stats[section].keys()])}],'
            f'datasets: [{{'
            f'label: "Accuracy (%)",'
            f'data: [{", ".join([f"{stats['accuracy']}" for stats in topic_stats[section].values()])}],'
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

# Save the HTML report
with open('../archive/MUET_Entry_Test_Comprehensive_Report.html', 'w') as f:
    f.write(html_content)

print("Comprehensive report generated: MUET_Entry_Test_Comprehensive_Report.html")