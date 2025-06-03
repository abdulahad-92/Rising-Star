import json
import os
from datetime import datetime

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

def generate_html_report(student_data, questions, metadata, output_dir='reports'):
    performance = assess_performance(student_data, questions, metadata)
    section_stats, topic_stats = generate_stats(performance, metadata)

    total_questions = performance['summary']['total_questions']
    attempted = performance['summary']['attempted']
    correct = performance['summary']['correct']
    incorrect = performance['summary']['incorrect']
    skipped = performance['summary']['skipped']
    percentage = round((correct / total_questions * 100), 2)

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
    overall_accuracy = round((correct / total_questions * 100), 2)
    if overall_accuracy < 40:
        tips.append(("Overall Performance: Your score is below 40%. Focus on consistent daily practice across all sections.", "critical"))
    elif 40 <= overall_accuracy <= 70:
        tips.append(("Overall Performance: Your score is moderate (40-70%). Target weak areas with targeted practice.", "moderate"))
    else:
        tips.append(("Overall Performance: Excellent work with over 70%! Maintain momentum and refine skills.", "maintenance"))

    if any(area[0] == 'Mathematics' for area in weak_areas):
        tips.append(("Mathematics: Practice 15 problems daily on weak topics like Trigonometry or Calculus.", "critical"))
    if any(area[0] == 'Physics' for area in weak_areas):
        tips.append(("Physics: Solve 10 numerical problems daily on Mechanics or Electromagnetism.", "critical"))
    if any(area[0] == 'Chemistry' for area in weak_areas):
        tips.append(("Chemistry: Review Organic Chemistry or Acids and Bases with flashcards.", "critical"))
    if any(area[0] == 'English' for area in weak_areas):
        tips.append(("English: Improve vocabulary and grammar with daily reading and writing.", "critical"))
    if skipped > total_questions * 0.3:
        tips.append(("Time Management: You skipped over 30% of questions. Practice mock tests to improve pace.", "moderate"))

    # Multiple motivational quotes based on performance
    quotes = {
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
    quote_category = 'low' if overall_accuracy < 40 else 'moderate' if overall_accuracy <= 70 else 'high'
    selected_quotes = quotes[quote_category]

    report_date = datetime.now().strftime('%I:%M %p PKT on %B %d, %Y')

    # Data for charts
    overall_chart_data = [correct, incorrect, skipped]
    overall_chart_labels = ['Correct', 'Incorrect', 'Skipped']
    section_chart_data = [stats['accuracy'] for stats in section_stats.values()]
    section_chart_labels = list(section_stats.keys())

    # Topic-wise chart data per section with diverse colors
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

    tips_list = "".join([f'<li class="tip-{category}">{tip}</li>' for tip, category in tips])
    quotes_list = "".join([f'<p class="quote {"featured-quote" if i == 0 else ""}">{quote}</p>' for i, quote in enumerate(selected_quotes)])

    base_name = os.path.basename(json_file)
    student_id_parts = base_name.split('_')
    student_id = student_id_parts[2] if len(student_id_parts) > 2 and student_id_parts[0] == 'student' and student_id_parts[1] == 'answers' else student_data.get('student_id', 'unknown')

    # Check if there are no weaknesses for the student
    has_weaknesses = len(weak_series) > 0 and sum(weak_series) > 0
    weak_content = '''
        <div class="chart-container strength-weakness-container" id="weakDonutChart"></div>
    ''' if has_weaknesses else '''
        <div class="chart-container strength-weakness-container no-weakness-message">
            <p class="no-weakness-text">Congratulations! No weaknesses identified. Keep up the excellent work!</p>
        </div>
    '''

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MUET Entry Test Report - {student_id}</title>
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
            }}
            @keyframes spin {{
                0% {{ transform: translate(-50%, -50%) rotate(0deg); }}
                100% {{ transform: translate(-50%, -50%) rotate(360deg); }}
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
        </style>
    </head>
    <body>
        <div class="download-btn">
            <button class="btn btn-primary" onclick="downloadPDF()">Download as PDF</button>
        </div>
        <div class="container" id="content-to-pdf">
            <h1>MUET Entry Test Performance Report</h1>
            <h2>Test Date: May 24, 2025 | Report Generated: {report_date}</h2>

            <div class="section summary-card" id="section-summary">
                <h3>Quick Summary</h3>
                <p class="summary-text">Score: {correct}/{total_questions} ({percentage:.2f}%)</p>
                <p class="summary-text">Top Strength: {highest_section[0]} ({highest_section[1]['accuracy']:.2f}%)</p>
                <p class="summary-text">Critical Weak Area: {most_critical[0]} - {most_critical[1]} ({most_critical[2]['accuracy']:.2f}%)</p>
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

            // Donut Chart for Weak Areas (only render if there are weaknesses)
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

            // Download PDF Functionality
            async function downloadPDF() {{
                console.log("Initializing jsPDF...");
                const {{ jsPDF }} = window.jspdf;
                if (!jsPDF) {{
                    console.error("jsPDF is not loaded!");
                    return;
                }}
                const doc = new jsPDF({{
                    orientation: 'portrait',
                    unit: 'mm',
                    format: 'a4'
                }});

                // Store original viewport width and styles
                const originalWidth = window.innerWidth;
                const originalDocWidth = document.documentElement.style.width;
                const originalBodyWidth = document.body.style.width;

                // Force viewport to large screen size for consistent rendering
                window.innerWidth = 1400;
                document.documentElement.style.width = '1400px';
                document.body.style.width = '1400px';

                // Trigger resize event to ensure elements adjust
                window.dispatchEvent(new Event('resize'));

                // Wait for a short moment to allow rendering
                await new Promise(resolve => setTimeout(resolve, 500));

                // Capture title and subheading
                const titleElement = document.querySelector('h1');
                const subheadingElement = document.querySelector('h2');
                const tempTitleDiv = document.createElement('div');
                tempTitleDiv.style.width = '1400px'; // Match container max-width
                tempTitleDiv.style.textAlign = 'center';
                const clonedTitle = titleElement.cloneNode(true);
                const clonedSubheading = subheadingElement.cloneNode(true);
                clonedSubheading.style.marginTop = '10px';
                tempTitleDiv.appendChild(clonedTitle);
                tempTitleDiv.appendChild(clonedSubheading);
                document.body.appendChild(tempTitleDiv);

                const titleCanvas = await html2canvas(tempTitleDiv, {{
                    scale: 2,
                    useCORS: true,
                    width: 1400,
                    height: tempTitleDiv.scrollHeight
                }});
                const titleImgData = titleCanvas.toDataURL('image/jpeg', 0.98);
                const titleImgWidth = 190; // A4 width minus margins
                const titleImgHeight = (titleCanvas.height * titleImgWidth) / titleCanvas.width;

                let currentY = 10;
                doc.addImage(titleImgData, 'JPEG', 10, currentY, titleImgWidth, titleImgHeight);
                currentY += titleImgHeight + 10; // Add gap after title

                // Remove temp div
                document.body.removeChild(tempTitleDiv);

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

                for (let i = 0; i < sections.length; i++) {{
                    const section = document.getElementById(sections[i]);
                    if (!section) continue;

                    // Use html2canvas to capture the section with fixed width
                    const canvas = await html2canvas(section, {{
                        scale: 2,
                        useCORS: true,
                        width: 1400, // Fixed width to match container max-width
                        height: section.scrollHeight
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
                }}

                // Restore original viewport width and styles
                window.innerWidth = originalWidth;
                document.documentElement.style.width = originalDocWidth;
                document.body.style.width = originalBodyWidth;
                window.dispatchEvent(new Event('resize'));

                doc.save(`MUET_Entry_Test_Report_${student_id}.pdf`);
            }}
        </script>
    </body>
    </html>
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    html_path = os.path.join(output_dir, f'MUET_Entry_Test_Report_{student_id}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated HTML report for {json_file}: {html_path}")
    return html_path

metadata_path = 'metadata_mock_test_16.json'
questions_path = 'questions.json'
metadata = load_metadata(metadata_path)
questions = load_questions(questions_path)

json_files = [f for f in os.listdir('.') if f.endswith('.json') and f != metadata_path and f != questions_path]

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        student_data = json.load(f)
    report_path = generate_html_report(student_data, questions, metadata)
    print(f"Generated report for {json_file}: {report_path}")