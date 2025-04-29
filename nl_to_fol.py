import re
from openai_clients import *
import json
import time

def format_output(text):
    # match = re.search(r'"premise"^,}]*', text)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    text = text.replace('```','').strip()
    if (text[-1]=='}'): text = text[:-1]
    index = text.find('"premise"')
    if index!=-1:
        return f"{{{text[index:]}}}"
    else:
        raise ValueError(f"Format wrong!")

def nl_to_fol(premises, question):
    # Construct a consistent and instructive prompt
    system_message = (
        "You are a world-class expert in Formal Logic and AI prompt engineering. "
        "Your task is to convert natural language premises into consistent First-Order Logic (FOL) formulas. "
        "Maintain full consistency between all premises. "
        "Use standard FOL symbols: ∧ for 'and', ∨ for 'or', → for 'implies', ¬ for 'not', ForAll(x, ...). "
        "Keep the variables meaningful (e.g., use 'c' for curriculum, 'f' for faculty, etc.). "
        "Use standardized predicate names, e.g., well_structured(c), enhances_engagement(c), can_enroll_organic_chemistry(student). "
        "For universal rules, use ForAll, ForAll(x, ...) (e.g. keyword 'everyone', keyword 'If', etc.)."
        "For facts, state directly without ForAll."
        "The question's predicate names must be in premises"
    )
    input_format = """
    Output format must exactly match:
    "premise": [
      "FOL statement 1",
      "FOL statement 2",
      ...
    ],
    "question": "FOL question"
    """

    # Build few-shot examples to make the model more accurate
    examples = """Example 1:
Input:
"premise": [
    "If a curriculum is well-structured and has exercises, it enhances student engagement.",
    "If a curriculum enhances student engagement and provides access to advanced resources, it enhances critical thinking.",
    "If a faculty prioritizes pedagogical training and curriculum development, the curriculum is well-structured.",
    "The faculty prioritizes pedagogical training and curriculum development.",
    "The curriculum has practical exercises.",
    "The curriculum provides access to advanced resources."
],
"question": "Does the combination of faculty priorities and curriculum features lead to enhanced critical thinking, according to the premises?"
Output:
"premise": [
    "ForAll(c, (well_structured(c) ∧ has_exercises(c)) → enhances_engagement(c))",
    "ForAll(c, (enhances_engagement(c) ∧ advanced_resources(c)) → enhances_critical_thinking(c))",
    "ForAll(f, (pedagogical_training(f) ∧ curriculum_development(f)) → well_structured(curriculum))",
    "pedagogical_training(faculty) ∧ curriculum_development(faculty)",
    "has_exercises(curriculum)",
    "advanced_resources(curriculum)"
],
"question": "enhances_critical_thinking(curriculum)"

Example 2:
Input:
"premise": [
    "Alex has completed safety orientation.",
    "Alex has a membership duration of 8 months.",
    "Alex has paid annual fees on time.",
    "If a person has a valid membership card and has completed safety orientation, they can use equipment.",
    "If a person can use equipment and has a trainer, they can book training.",
    "If a person’s membership duration is at least 6 months, they are eligible for a trainer.",
    "If a person has paid the annual fee, they have a valid membership."
],
"question": "Does Alex meet all requirements for booking training sessions, according to the premises?"
Output:
"premise": [
    "safety_orientation(Alex)",
    "membership_duration(Alex) = 8",
    "paid_annual_fee(Alex)",
    "ForAll(x, (valid_membership(x) ∧ safety_orientation(x)) → use_equipment(x))",
    "ForAll(x, (use_equipment(x) ∧ has_trainer(x)) → book_training(x))",
    "ForAll(x, (membership_duration(x) ≥ 6) → eligible_trainer(x))",
    "ForAll(x, paid_annual_fee(x) → valid_membership(x))"
],
"question": "book_training(Alex)"

Example 3:
Input:
"premise": [
    "If a student is enrolled in a science program and has passed Chemistry 101, they can enroll in Organic Chemistry.",
    "If a student is enrolled in Organic Chemistry and has completed Lab Safety Certification, they can access the advanced lab.",
    "All students who complete Organic Chemistry can take Biochemistry.",
    "If course X is a prerequisite for course Y, and course Y is a prerequisite for course Z, then course X is a prerequisite for course Z.",
    "Minh is enrolled in a science program.",
    "Minh passed Chemistry 101.",
    "Minh completed Organic Chemistry.",
    "Minh completed Lab Safety Certification."
],
"question": "Does Minh qualify to take Biochemistry based on her completed coursework, according to the premises?"
Output:
"premise": [
    "ForAll(x, (science_program(x) ∧ passed(x, Chem101)) → can_enroll(x, OrganicChem))",
    "ForAll(x, (enrolled(x, OrganicChem) ∧ completed(x, LabSafety)) → lab_access(x))",
    "ForAll(x, completed(x, OrganicChem) → can_take(x, Biochemistry))",
    "ForAll(a, ForAll(b, ForAll(c, (prereq(a, b) ∧ prereq(b, c)) → prereq(a, c))))",
    "science_program(Minh)",
    "passed(Minh, Chem101)",
    "completed(Minh, OrganicChem)",
    "completed(Minh, LabSafety)"
],
"question": "can_take(x, Biochemistry)"
"""
    # Turn the user's input list into a JSON-style array
    # user_input = "Input:\n" + json.dumps(inputs, indent=4)
    user_prompt = f"""Input:
"premise": {premises},
"question": "{question}"
Output:"""

    # Full prompt
    full_prompt = system_message + "\n\n" + input_format + "\n\n" + examples + "\n\n" + user_prompt + "\nOutput:"
    # print(full_prompt)
    # Call the model
    response = client.chat.completions.create(
        model=model_name,  # or a strong model you have access to
        messages=[
            {"role": "system", "content": system_message+"\n"+input_format},
            {"role": "user", "content": examples},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,  # deterministic output
        max_tokens=1000,
        stream=False
    )

    # Extract the output text
    output_text = response.choices[0].message.content.strip()

    # Optionally parse the output to Python list
    # print(output_text)
    output_text = format_output(output_text) 
    # print('after format_output:',output_text)
    
    try:
        fol_output = json.loads(output_text)
        return fol_output
    except json.JSONDecodeError:
        print("Warning: Output not in JSON format. Returning raw text.")
        return output_text

if __name__ == "__main__":
    inputs = [
        "All students attend lectures.",
		"At least one student is part of a research group.",
		"All students complete their assignments.",
		"If at least one student is part of a research group, then all students attend lectures.",
		"If all students attending lectures implies that all students complete their assignments, then all students complete their assignments.",
		"At least one student participates in extracurricular activities.",
		"If a student is part of a research group, then they also complete their assignments."
	]
    question = "Do all students participate in extracurricular activities?"
    output = nl_to_fol(inputs, question)
    print(output)