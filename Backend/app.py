from flask import Flask, request, jsonify, session
import spacy
import re

# Initialize Flask app
app = Flask(__name__)
app.secret_key = ""  # Required for session management

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Sample knowledge base
knowledge_base = {
    "not charging": [
        {
            "question": "Are there any lights blinking on the charging station?",
            "yes": "Check the power source and ensure the station is working properly.",
            "no": "Ensure the cable is properly connected to both the car and the charger.",
        },
        {
            "question": "Is the charging cable damaged?",
            "yes": "Replace the cable with a new one.",
            "no": "Try resetting the charging station or the vehicle software.",
        },
    ],
    "low range": [
        {
            "question": "Have you recently updated your vehicle software?",
            "yes": "Check if the update has range optimizations.",
            "no": "Update your vehicle software to the latest version.",
        },
        {
            "question": "Are you using climate control heavily?",
            "yes": "Reduce climate control usage to conserve battery.",
            "no": "Visit a service center to check the battery health.",
        },
    ],
    "starting": [
        {
            "question": "Is the battery fully charged?",
            "yes": "Check the ignition system and starter motor.",
            "no": "Charge the battery fully and try again."
        },
        {
            "question": "Are there any error messages on the dashboard?",
            "yes": "Refer to the owner's manual for specific error codes.",
            "no": "Inspect fuses and circuit breakers for issues."
        }
    ],
}

def extract_keywords(user_input):
    """Extract keywords using spaCy for matching issues."""
    doc = nlp(user_input)
    issues = []

    for token in doc:
        if token.text.lower() in {"charging", "range", "battery", "power", "not", "low","starting"}:
            issues.append(token.text.lower())
    return " ".join(issues).strip()

def match_issue(extracted_issue):
    """Match the issue to a known problem."""
    for issue in knowledge_base.keys():
        if re.search(issue, extracted_issue, re.IGNORECASE):
            return issue
    return None

@app.route('/troubleshoot', methods=['POST'])
def troubleshoot():
    data = request.json
    user_input = data.get('issue', '').strip().lower()

    # If no session exists, treat this as the first input
    if "current_issue" not in session or "current_step" not in session:
        extracted_issue = extract_keywords(user_input)
        matched_issue = match_issue(extracted_issue)

        if matched_issue:
            session["current_issue"] = matched_issue
            session["current_step"] = 0
            session["awaiting_resolution_check"] = False
            question = knowledge_base[matched_issue][0]["question"]
            return jsonify({"response": question})
        else:
            return jsonify({"error": "Issue not recognized. Please provide more details."}), 400

    # If awaiting resolution confirmation
    if session.get("awaiting_resolution_check", False):
        if user_input == "yes":
            session.clear()
            return jsonify({"response": "Thank you. Session has been reset."})
        elif user_input == "no":
            current_issue = session["current_issue"]
            current_step = session["current_step"]
            steps = knowledge_base[current_issue]

            # Check if there are more questions
            if current_step + 1 < len(steps):
                session["current_step"] += 1  # Increment to the next step
                session["awaiting_resolution_check"] = False  # Back to normal flow
                next_question = steps[session["current_step"]]["question"]
                return jsonify({"response": "Let's continue troubleshooting.", "next_question": next_question})
            else:
                session.clear()
                return jsonify({"response": "Contact your nearest service center. Session has been reset."})
        else:
            return jsonify({"error": "Please respond with 'yes' or 'no'."}), 400

    # Handle yes/no responses for ongoing sessions
    current_issue = session["current_issue"]
    current_step = session["current_step"]
    steps = knowledge_base[current_issue]

    if user_input in ["yes", "no"]:
        response = steps[current_step][user_input]

        # Check if there are more steps
        if current_step + 1 < len(steps):
            session["awaiting_resolution_check"] = True
            return jsonify({"response": response, "next_question": "Is the problem solved?"})
        else:
            # Last step, ask if resolved
            session["awaiting_resolution_check"] = True
            return jsonify({"response": response, "next_question": "Is the problem solved?"})
    else:
        return jsonify({"error": "Please respond with 'yes' or 'no'."}), 400

@app.route('/reset', methods=['POST'])
def reset_session():
    """Resets the troubleshooting session."""
    session.clear()
    return jsonify({"message": "Session reset. Start troubleshooting again."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)