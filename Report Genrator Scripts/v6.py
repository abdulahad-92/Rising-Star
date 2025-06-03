import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def load_data(filename):
    try:
        with open(filename, 'rb') as file:
            content = file.read()

        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            print("Warning: UTF-8 decoding failed, falling back to Latin-1.")
            text = content.decode('latin1')

        return json.loads(text)

    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        return None

def load_metadata(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file {filename} contains invalid JSON.")
        return None


def normalize_data(data):
    """Normalize different data structures into a consistent format."""
    if not data:
        return None

    normalized = {}
    if isinstance(data, list):
        # Structure: [{"id": 1, ...}, {"id": 2, ...}, ...]
        for q in data:
            q_id = q.get("id")
            if q_id is not None:
                key = f"q{q_id}"
                if key not in normalized:
                    normalized[key] = []
                normalized[key].append(q)
    elif "questions" in data:
        questions = data["questions"]
        if isinstance(questions, dict):
            # Structure: {"questions": {"1": [...], "2": [...], ...}}
            for key, q_list in questions.items():
                normalized[f"q{key}"] = q_list
        elif isinstance(questions, list):
            # Structure: {"questions": [{"id": 1, ...}, {"id": 2, ...}, ...]}
            for q in questions:
                q_id = q.get("id")
                if q_id is not None:
                    key = f"q{q_id}"
                    if key not in normalized:
                        normalized[key] = []
                    normalized[key].append(q)
        else:
            print("Error: 'questions' field in JSON has an unsupported format.")
            return None
    else:
        # Structure: {"q1": [...], "q2": [...], ...}
        if all(key.startswith("q") and key[1:].isdigit() for key in data.keys()):
            normalized = data
        else:
            print("Error: JSON data does not contain 'questions' field or expected 'qN' keys.")
            return None
    return normalized


def generate_report(data, metadata, filename='MUET_Entry_Test_Report.pdf'):
    # Normalize the data
    data = normalize_data(data)
    if not data:
        print("Error: Could not process the data. Please check the structure of questions.json.")
        return

    # Calculate total questions by counting all questions across sections
    total_questions = sum(len(questions) for questions in data.values())
    if total_questions == 0:
        print("Error: No questions found in the data.")
        return

    # Calculate overall statistics
    attempted = sum(1 for questions in data.values() for q in questions if q.get('response', '') != '')
    correct = sum(1 for questions in data.values() for q in questions if q.get('response', '') == q.get('answer', ''))
    incorrect = sum(1 for questions in data.values() for q in questions if
                    q.get('response', '') != q.get('answer', '') and q.get('response', '') != '')
    skipped = total_questions - attempted
    percentage = (correct / total_questions) * 100 if total_questions > 0 else 0

    # Section-wise and topic-wise stats
    section_stats = {}
    topic_stats = {}
    for section, info in metadata['sections'].items():
        start, end = info['range']
        section_questions = sum(len(data.get(f"q{i}", [])) for i in range(start, end + 1))
        section_attempted = sum(
            1 for i in range(start, end + 1) for q in data.get(f"q{i}", []) if q.get('response', '') != '')
        section_correct = sum(1 for i in range(start, end + 1) for q in data.get(f"q{i}", []) if
                              q.get('response', '') == q.get('answer', ''))
        section_incorrect = sum(1 for i in range(start, end + 1) for q in data.get(f"q{i}", []) if
                                q.get('response', '') != q.get('answer', '') and q.get('response', '') != '')
        section_skipped = section_questions - section_attempted
        accuracy = (section_correct / section_questions) * 100 if section_questions > 0 else 0
        section_stats[section] = {
            'attempted': section_attempted,
            'correct': section_correct,
            'incorrect': section_incorrect,
            'skipped': section_skipped,
            'accuracy': accuracy
        }

        topic_stats[section] = {}
        for i in range(start, end + 1):
            for q in data.get(f"q{i}", []):
                topic = q.get('topic', 'Unknown')
                if topic not in topic_stats[section]:
                    topic_stats[section][topic] = {'attempted': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0}
                topic_stats[section][topic]['attempted'] += 1 if q.get('response', '') != '' else 0
                topic_stats[section][topic]['correct'] += 1 if q.get('response', '') == q.get('answer', '') else 0
                topic_stats[section][topic]['incorrect'] += 1 if q.get('response', '') != q.get('answer', '') and q.get(
                    'response', '') != '' else 0
                topic_stats[section][topic]['skipped'] += 1 if q.get('response', '') == '' else 0
                topic_stats[section][topic]['accuracy'] = (topic_stats[section][topic]['correct'] / (
                            topic_stats[section][topic]['attempted'] or 1)) * 100

    # Identify weak and strength areas
    weak_areas = []
    strength_areas = []
    for section, topics in topic_stats.items():
        for topic, stats in topics.items():
            if stats['accuracy'] < 70 or stats['skipped'] >= 2:
                weak_areas.append((section, topic, stats))
            elif stats['accuracy'] >= 90 and stats['attempted'] >= 5 and stats['attempted'] < 25:
                strength_areas.append((section, topic, stats))
    strength_areas = strength_areas[:5]

    # Generate tips
    tips = []
    if percentage < 70:
        tips.append("\\item Overall Performance: Aim for over 70\\%. Increase daily practice by 2 hours.")
    else:
        tips.append("\\item Overall Performance: Excellent work with over 70\\%! Maintain momentum and refine skills.")

    # Motivational quote
    quote = "The only way to do great work is to love what you do. - Steve Jobs"

    # Generate radar chart for section-wise performance
    labels = list(section_stats.keys())
    values = [stats['accuracy'] for stats in section_stats.values()]
    values += values[:1]  # Close the loop for radar chart
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_title("Section-wise Accuracy (%)", size=15, color='blue', y=1.1)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    radar_chart = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Generate heatmap for topic-wise performance
    sections = list(topic_stats.keys())
    all_topics = set()
    for section in sections:
        all_topics.update(topic_stats[section].keys())
    all_topics = sorted(list(all_topics))
    heatmap_data = np.zeros((len(sections), len(all_topics)))
    for i, section in enumerate(sections):
        for j, topic in enumerate(all_topics):
            heatmap_data[i, j] = topic_stats[section].get(topic, {'accuracy': 0})['accuracy']

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="YlGnBu", xticklabels=all_topics, yticklabels=sections)
    ax.set_title("Topic-wise Accuracy Heatmap (%)")
    plt.xticks(rotation=45, ha='right')

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    heatmap = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Generate SVG for progress circle
    angle = (percentage / 100) * 360
    large_arc_flag = 1 if angle > 180 else 0
    end_x = 50 + 40 * np.cos(np.radians(angle - 90))
    end_y = 50 + 40 * np.sin(np.radians(angle - 90))
    path = f"M 50,10 A 40,40 0 {large_arc_flag},1 {end_x},{end_y}" if percentage < 100 else "M 50,10 A 40,40 0 1,1 49.99,10"
    progress_circle = fr"""
    \begin{{svg}}
    <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#e0e6ed" stroke-width="10"/>
        <path d="{path}" fill="none" stroke="#4CAF50" stroke-width="10" stroke-linecap="round"/>
        <text x="50" y="55" font-size="20" text-anchor="middle">{percentage:.1f}\%</text>
    </svg>
    \end{{svg}}
    """

    # Generate tables
    section_table = "".join([
        f"\\hline {section} (Q{start}--{end}) & {end - start + 1} & {stats['attempted']} & {stats['correct']} & {stats['incorrect']} & {stats['skipped']} & {stats['accuracy']:.2f}\\% \\\\"
        for section, (start, end), stats in
        [(sec, (data["range"][0], data["range"][1]), section_stats[sec]) for sec, data in metadata['sections'].items()]
    ])
    weak_table = "".join([
        f"\\hline {section} & {topic} & {stats['attempted']} & {stats['correct']} & {stats['incorrect']} & {stats['skipped']} & {stats['accuracy']:.2f}\\% & " +
        (
            'Critical: Accuracy < 20\\% or high skips. Practice 20 problems daily on ' + topic.lower() + ' using Khan Academy or textbooks.' if
            stats["accuracy"] < 20 or stats["skipped"] >= 2 else
            'Moderate: Accuracy 20\\%-50\\%. Solve 10 problems daily and review concepts.' if 20 <= stats[
                "accuracy"] < 50 else
            'Mild: Accuracy 50\\%-70\\%. Review with 5 problems daily.') + " \\\\"
        for section, topic, stats in weak_areas
    ]) or "\\hline \\multicolumn{8}{|c|}{No significant weak areas identified. Keep up the good work!} \\\\"
    strength_table = "".join([
        f"\\hline {section} & {topic} & {stats['attempted']} & {stats['correct']} & {stats['incorrect']} & {stats['skipped']} & {stats['accuracy']:.2f}\\% & Excellent performance! Maintain by practicing 5 problems weekly. \\\\"
        for section, topic, stats in strength_areas
    ]) or "\\hline \\multicolumn{8}{|c|}{No standout strengths yet. Aim for consistency!} \\\\"
    tips_list = "".join([f"\\item {tip}" for tip in
                         tips]) or "\\item No specific tips at this time. Continue your current study approach."

    # LaTeX document
    latex_content = fr"""
    \\documentclass[a4paper,12pt]{{article}}
    \\usepackage[utf8]{{inputenc}}
    \\usepackage{{geometry}}
    \\usepackage{{graphicx}}
    \\usepackage{{svg}}
    \\usepackage{{booktabs}}
    \\usepackage{{array}}
    \\usepackage{{colortbl}}
    \\usepackage{{xcolor}}
    \\usepackage{{sectsty}}
    \\allsectionsfont{{\\color{{blue!70!black}}}}
    \\geometry{{margin=1in}}
    \\begin{{document}}
    \\begin{{center}}
    \\Huge{{MUET Entry Test Performance Report}}\\\\
    \\normalsize{{Test Date: May 24, 2025 | Report Generated: May 24, 2025}}
    \\end{{center}}

    \\section*{{Overall Performance Summary}}
    \\begin{{tabular}}{{ll}}
    \\textbf{{Total Questions:}} & {total_questions} \\\\
    \\textbf{{Attempted Questions:}} & {attempted} \\\\
    \\textbf{{Correct Answers:}} & {correct} \\\\
    \\textbf{{Incorrect Answers:}} & {incorrect} \\\\
    \\textbf{{Skipped Questions:}} & {skipped} \\\\
    \\textbf{{Score:}} & {correct} out of {total_questions} \\\\
    \\end{{tabular}}

    \\begin{{center}}
    {progress_circle}
    \\end{{center}}

    \\section*{{Section-wise Performance}}
    \\begin{{tabular}}{{|l|c|c|c|c|c|c|}}
    \\hline
    \\textbf{{Section}} & \\textbf{{Questions}} & \\textbf{{Attempted}} & \\textbf{{Correct}} & \\textbf{{Incorrect}} & \\textbf{{Skipped}} & \\textbf{{Accuracy}} \\\\
    {section_table}
    \\hline
    \\end{{tabular}}

    \\begin{{center}}
    \\includegraphics[width=0.6\\textwidth]{{data:image/png;base64,{radar_chart}}}
    \\end{{center}}

    \\section*{{Topic-wise Performance}}
    \\begin{{center}}
    \\includegraphics[width=0.9\\textwidth]{{data:image/png;base64,{heatmap}}}
    \\end{{center}}

    \\section*{{Weak Areas}}
    \\begin{{tabular}}{{|l|l|c|c|c|c|c|p{{4cm}}|}}
    \\hline
    \\textbf{{Section}} & \\textbf{{Topic}} & \\textbf{{Attempted}} & \\textbf{{Correct}} & \\textbf{{Incorrect}} & \\textbf{{Skipped}} & \\textbf{{Accuracy}} & \\textbf{{Recommendation}} \\\\
    {weak_table}
    \\hline
    \\end{{tabular}}

    \\section*{{Strengths}}
    \\begin{{tabular}}{{|l|l|c|c|c|c|c|p{{3cm}}|}}
    \\hline
    \\textbf{{Section}} & \\textbf{{Topic}} & \\textbf{{Attempted}} & \\textbf{{Correct}} & \\textbf{{Incorrect}} & \\textbf{{Skipped}} & \\textbf{{Accuracy}} & \\textbf{{Insight}} \\\\
    {strength_table}
    \\hline
    \\end{{tabular}}

    \\section*{{Tips for Improvement}}
    \\begin{{itemize}}
    {tips_list}
    \\end{{itemize}}

    \\section*{{Keep Going!}}
    {quote}

    \\end{{document}}
    """

def main():
    data = load_data('questions.json')
    metadata = load_metadata('metadata_clean.json')
    if data and metadata:
        generate_report(data, metadata)

if __name__ == "__main__":
    main()

