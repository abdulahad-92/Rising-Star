import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
import subprocess
from datetime import datetime

# Ensure the reports directory exists
REPORTS_DIR = "reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)


def load_data(filename):
    try:
        with open(filename, 'rb') as file:
            content = file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            print(f"Warning: UTF-8 decoding failed for {filename}, falling back to Latin-1.")
            text = content.decode('latin1')
        return json.loads(text)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filename} - {e}")
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


def get_topic_for_question(q_id, metadata):
    """Assign a topic to a question based on its ID and metadata."""
    for section, info in metadata['sections'].items():
        start, end = info['range']
        if start <= q_id <= end:
            topics = info['topics']
            for key, topic in topics.items():
                if '-' in key:  # Range like "1-2"
                    range_start, range_end = map(int, key.split('-'))
                    if range_start <= q_id <= range_end:
                        return topic
                else:  # Single question like "3"
                    if int(key) == q_id:
                        return topic
    return "Unknown"


def merge_student_answers(questions, student_answers, metadata):
    """Merge student answers with questions data and assign topics."""
    if not questions or not student_answers:
        return None

    # Create a dictionary of questions by ID
    question_dict = {q['id']: q.copy() for q in questions}

    # Process student answers
    student_answers = student_answers.get('answers', [])
    for answer in student_answers:
        q_id = answer.get('id')
        if q_id in question_dict:
            question_dict[q_id]['response'] = answer.get('selected_option', '')
            # Assign topic based on metadata
            question_dict[q_id]['topic'] = get_topic_for_question(q_id, metadata)

    # Convert back to list format for consistency
    merged_data = [
        {
            'id': q['id'],
            'question': q['question'],
            'options': q['options'],
            'answer': q['answer'],
            'topic': q.get('topic', 'Unknown'),
            'response': q.get('response', '')
        }
        for q in question_dict.values()
    ]
    return merged_data


def normalize_data(data):
    """Normalize data into a dictionary with keys q1, q2, etc."""
    if not data:
        return None

    normalized = {}
    if isinstance(data, list):
        for q in data:
            q_id = q.get("id")
            if q_id is not None:
                key = f"q{q_id}"
                if key not in normalized:
                    normalized[key] = []
                normalized[key].append(q)
    else:
        print("Error: Expected a list of questions in data.")
        return None
    return normalized


def generate_report(student_data, metadata, student_id, filename):
    # Normalize the data
    data = normalize_data(student_data)
    if not data:
        print(f"Error: Could not process data for student {student_id}.")
        return

    # Calculate total questions
    total_questions = sum(len(questions) for questions in data.values())
    if total_questions == 0:
        print(f"Error: No questions found for student {student_id}.")
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
        [(sec, metadata['sections'][sec]["range"], section_stats[sec]) for sec in metadata['sections']]
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
    current_date = datetime.now().strftime("%B %d, %Y")
    latex_content = fr"""
    \documentclass[a4paper,12pt]{{article}}
    \usepackage[utf8]{{inputenc}}
    \usepackage{{geometry}}
    \usepackage{{graphicx}}
    \usepackage{{svg}}
    \usepackage{{booktabs}}
    \usepackage{{array}}
    \usepackage{{colortbl}}
    \usepackage{{xcolor}}
    \usepackage{{sectsty}}
    \allsectionsfont{{\color{{blue!70!black}}}}
    \geometry{{margin=1in}}
    \begin{{document}}
    \begin{{center}}
    \Huge{{MUET Entry Test Performance Report}}\\\\
    \normalsize{{Student ID: {student_id} | Test Date: May 24, 2025 | Report Generated: {current_date}}}
    \end{{center}}

    \section*{{Overall Performance Summary}}
    \begin{{tabular}}{{ll}}
    \textbf{{Total Questions:}} & {total_questions} \\\\
    \textbf{{Attempted Questions:}} & {attempted} \\\\
    \textbf{{Correct Answers:}} & {correct} \\\\
    \textbf{{Incorrect Answers:}} & {incorrect} \\\\
    \textbf{{Skipped Questions:}} & {skipped} \\\\
    \textbf{{Score:}} & {correct} out of {total_questions} \\\\
    \end{{tabular}}

    \begin{{center}}
    {progress_circle}
    \end{{center}}

    \section*{{Section-wise Performance}}
    \begin{{tabular}}{{|l|c|c|c|c|c|c|}}
    \hline
    \textbf{{Section}} & \textbf{{Questions}} & \textbf{{Attempted}} & \textbf{{Correct}} & \textbf{{Incorrect}} & \textbf{{Skipped}} & \textbf{{Accuracy}} \\\\
    {section_table}
    \hline
    \end{{tabular}}

    \begin{{center}}
    \includegraphics[width=0.6\textwidth]{{data:image/png;base64,{radar_chart}}}
    \end{{center}}

    \section*{{Topic-wise Performance}}
    \begin{{center}}
    \includegraphics[width=0.9\textwidth]{{data:image/png;base64,{heatmap}}}
    \end{{center}}

    \section*{{Weak Areas}}
    \begin{{tabular}}{{|l|l|c|c|c|c|c|p{{4cm}}|}}
    \hline
    \textbf{{Section}} & \textbf{{Topic}} & \textbf{{Attempted}} & \textbf{{Correct}} & \textbf{{Incorrect}} & \textbf{{Skipped}} & \textbf{{Accuracy}} & \textbf{{Recommendation}} \\\\
    {weak_table}
    \hline
    \end{{tabular}}

    \section*{{Strengths}}
    \begin{{tabular}}{{|l|l|c|c|c|c|c|p{{3cm}}|}}
    \hline
    \textbf{{Section}} & \textbf{{Topic}} & \textbf{{Attempted}} & \textbf{{Correct}} & \textbf{{Incorrect}} & \textbf{{Skipped}} & \textbf{{Accuracy}} & \textbf{{Insight}} \\\\
    {strength_table}
    \hline
    \end{{tabular}}

    \section*{{Tips for Improvement}}
    \begin{{itemize}}
    {tips_list}
    \end{{itemize}}

    \section*{{Keep Going!}}
    {quote}

    \end{{document}}
    """
        # Save LaTeX content to a .tex file in the reports directory
    tex_filename = os.path.join(REPORTS_DIR, filename.replace('.pdf', '.tex'))
    pdf_filename = os.path.join(REPORTS_DIR, filename)
    with open(tex_filename, 'w', encoding='utf-8') as f:
        f.write(latex_content)

        # Compile to PDF using pdflatex with multiple passes
        try:
            pdflatex_path = r"C:\Users\DENZEN COMPUTER\MiKTeX\miktex\bin\x64\pdflatex.exe"
            # Verify the pdflatex executable exists
            if not os.path.isfile(pdflatex_path):
                raise FileNotFoundError(f"pdflatex executable not found at {pdflatex_path}. Please verify the path.")

            print(f"Starting compilation for student {student_id} at {datetime.now().strftime('%H:%M:%S')}...")
            for pass_num in range(2):  # Run twice to resolve references
                print(
                    f"Running pdflatex pass {pass_num + 1} for {student_id} at {datetime.now().strftime('%H:%M:%S')}...")
                result = subprocess.run(
                    [pdflatex_path, '-output-directory', REPORTS_DIR, tex_filename],
                    check=True,
                    capture_output=True,
                    text=True
                )
                # Print pdflatex output for debugging
                if result.stderr:
                    print(
                        f"pdflatex stderr for {student_id}, pass {pass_num + 1} at {datetime.now().strftime('%H:%M:%S')}: {result.stderr}")
                if result.stdout:
                    print(
                        f"pdflatex stdout for {student_id}, pass {pass_num + 1} at {datetime.now().strftime('%H:%M:%S')}: {result.stdout}")
            # Check if PDF was generated
            if not os.path.exists(pdf_filename):
                raise FileNotFoundError(f"PDF not generated at {pdf_filename}. Check LaTeX errors above.")
            print(
                f"Report generated successfully for student {student_id} at {pdf_filename} at {datetime.now().strftime('%H:%M:%S')}")
            # Clean up auxiliary files
            for ext in ['aux', 'log', 'out', 'tex']:
                file_to_remove = os.path.join(REPORTS_DIR, f"{filename.replace('.pdf', '')}.{ext}")
                if os.path.exists(file_to_remove):
                    os.remove(file_to_remove)
        except subprocess.CalledProcessError as e:
            print(
                f"Error compiling LaTeX to PDF for student {student_id} at {datetime.now().strftime('%H:%M:%S')}: {e.stderr}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(
                f"Unexpected error during PDF compilation for student {student_id} at {datetime.now().strftime('%H:%M:%S')}: {e}")


def main():
    # Load questions and metadata
    questions = load_data('questions.json')
    metadata = load_metadata('metadata_clean.json')
    if not questions or not metadata:
        print("Error: Could not load questions.json or metadata_clean.json.")
        return

    # Find all student answer files
    student_files = glob.glob("student_answers_*.json")
    if not student_files:
        print("Error: No student answer files found in the directory.")
        return

    # Process each student file
    for student_file in student_files:
        student_data = load_data(student_file)
        if not student_data:
            continue

        # Extract student ID from filename
        student_id = student_file.replace("student_answers_", "").replace(".json", "")
        # Merge student answers with questions
        merged_data = merge_student_answers(questions, student_data, metadata)
        if not merged_data:
            print(f"Error: Could not merge data for student {student_id}.")
            continue

        # Generate report
        filename = f"MUET_Entry_Test_Report_{student_id}.pdf"
        generate_report(merged_data, metadata, student_id, filename)


if __name__ == "__main__":
    main()