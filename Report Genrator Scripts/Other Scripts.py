import json

# Paste the valid metadata dictionary here
clean_metadata = {
  "sections": {
    "Mathematics": {
      "range": [1, 25],
      "topics": {
        "1-2": "Trigonometry", "3": "Algebra", "4": "Combinatorics", "5": "Sequences and Series",
        "6": "Complex Numbers", "7": "Algebra", "8": "Logarithms", "9": "Calculus", "10": "Probability",
        "11": "Set Theory", "12": "Conic Sections", "13": "Trigonometry", "14": "Functions",
        "15": "Sequences and Series", "16": "Trigonometry", "17": "Algebra", "18": "Vectors",
        "19": "Exponents", "20": "Vectors", "21": "Geometry", "22": "Calculus", "23": "Statistics",
        "24": "Matrices", "25": "Sequences and Series"
      }
    },
    "Physics": {
      "range": [26, 50],
      "topics": {
        "26": "Mechanics", "27-28": "Quantum Mechanics", "29": "Dimensional Analysis", "30": "Mechanics",
        "31": "Optics", "32": "Electromagnetism", "33": "Mechanics", "34": "Electromagnetism",
        "35": "Waves", "36": "Quantum Mechanics", "37": "Thermodynamics", "38": "Electromagnetism",
        "39": "Nuclear Physics", "40": "Mechanics", "41": "Optics", "42": "Quantum Mechanics",
        "43": "Thermodynamics", "44": "Electromagnetism", "45": "Electromagnetism", "46": "Waves",
        "47": "Electromagnetism", "48": "Thermodynamics", "49": "Optics", "50": "Mechanics"
      }
    },
    "Chemistry": {
      "range": [51, 75],
      "topics": {
        "51-54": "Atomic Structure", "55-57": "Organic Chemistry", "58-60": "Acids and Bases",
        "61": "Chemical Bonding", "62": "Atomic Structure", "63": "Acids and Bases", "64": "Organic Chemistry",
        "65": "Stoichiometry", "66": "Organic Chemistry", "67": "Industrial Chemistry", "68": "Periodic Table",
        "69": "Chemical Bonding", "70": "Thermodynamics", "71": "Organic Chemistry",
        "72": "Physical Chemistry", "73": "Inorganic Chemistry", "74": "Physical Chemistry",
        "75": "Organic Chemistry"
      }
    },
    "English": {
      "range": [76, 100],
      "topics": {
        "76-79": "Vocabulary", "80-90": "Grammar", "91-95": "Sentence Correction", "96-100": "Vocabulary"
      }
    }
  },
  "total_questions": 100
}

# Write the new file
with open("metadata_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean_metadata, f, indent=2)
