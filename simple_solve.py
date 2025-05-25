import time
import json
import json
import re
from openai_clients import *
from test.use_retrieval import get_closest_strings
from timeout import *

def to_json(content):
    s = content.strip()
    s = re.sub(r'<think>.*?</think>', '', s, flags=re.DOTALL).strip()
    if s.startswith("```json"):
        s = s[7:-3]
    s = s.strip()
    if s[-1]!='}':
        s = s+'}'
    # print('final string:',s)
    return json.loads(s)

def solve_fol_problem_fullLM(premises_nl, question, start_time):
    body = {
        "premises-NL": premises_nl,
        "questions": [question]
    }
    response = solve_fol_problem_(body, start_time)
    return response 

def solve_fol_problem_(input_data, start_time, model=model_name, temperature=0.0, useRetrieval=True):
    """
    Solve FOL natural language problems with advanced reasoning.
    """
    premises = input_data["premises-NL"]
    questions = input_data["questions"]

    system_prompt = (
        "You are a world-class logician and AI researcher.\n"
        "Instructions:\n"
        "- Read the premises and the question carefully.\n"
        "- Identify the type of question automatically (Yes/No/Uncertain, number, or multiple-choice, etc.).\n"
        "- Reason step-by-step internally but DO NOT show internal thoughts.\n"
        "- Output ONLY a pure JSON object with exactly these fields:\n"
        "- Always reason step-by-step. Extract relevant premises.\n"
        "- Cross-verify reasoning before finalizing answer. Output must include answer choice, premise indices, and detailed explanation.\n"
        "- Use as FEW premises as possible.\n"
        "- If it is a multiple choice question then just ONlY show the idxs that the CORRECT answer uses.\n"
        "{\n"
        "  \"answer\": (Yes/No/Uncertain/number/letter A-D),\n"
        "  \"idx\": [list of integers],\n"
        "  \"explanation\": [list of strings, one per premise used]\n"
        "}\n"
        "- Make sure each 'idx' item matches exactly one explanation sentence.\n"
        "- Use only premises truly necessary for inference. No irrelevant ones.\n"
        "- No extra comments. No preambles. Only strict JSON output.\n"
    )
    examples = """
# Example 1:
Input:
{"premises-NL": [
    "There exists at least one student who has completed their assignments.",
    "There exists at least one student who participates in extracurricular activities.",
    "If a student follows the study plan, then they will pass the exam.",
    "Every student follows the attendance policy.",
    "There exists at least one student who has achieved high marks.",
    "If a student does not complete assignments, they will not pass the exam.",
    "If a student follows the attendance policy, then they will be eligible for participation points.",
    "If a student has completed assignments, then they will be eligible for extra credit.",
    "If a student follows the attendance policy, then they are eligible for participation points.",
    "If a student participates in extracurricular activities, then they will gain extra credit.",
    "If a student does not follow the attendance policy, then they will lose participation points.",
    "Every student participates in group projects."
],
"questions": [
    "Based on the above premises, which statement can be inferred?\nA. 'If a student participates in extracurricular activities and follows the attendance policy, they will gain extra credit and be eligible for participation points.'\nB. 'If a student does not complete assignments and does not follow the study plan, they will not pass the exam and not be eligible for extra credit.'\nC. 'If a student participates in group projects and does not follow the attendance policy, they will gain extra credit and lose participation points.'\nD. 'If a student follows the study plan and completes assignments, they will pass the exam and not be eligible for extra credit.'",
    "Based on the above premises, is the statement true?\nStatement: 'If a student does not complete assignments and does not follow the study plan, they will not pass the exam and not be eligible for extra credit.'"
]}
Output:
{"answers": [
    "B", "Yes"
],
"idx": [
    [3, 6, 8],
    [6, 8]
],
"explanation": [
    "From premise 6, we know that if a student does not complete assignments, they will not pass the exam. From premise 3, we know that if a student follows the study plan, they will pass the exam. From premise 8, we know that if a student has completed assignments, they will be eligible for extra credit. Therefore, if a student does not complete assignments and does not follow the study plan, they will not pass the exam (from premises 6 and 3) and not be eligible for extra credit (from premise 8), making option B correct.",
    "From premise 6, we know that if a student does not complete assignments, they will not pass the exam. From premise 8, we know that if a student has completed assignments, they will be eligible for extra credit. Therefore, if a student does not complete assignments and does not follow the study plan, they will not pass the exam (from premise 6) and not be eligible for extra credit (from premise 8), making the statement true."
]}
# Example 2:
Input:
{"premises-NL": [
    "Retaking for improvement is re-registering a previously passed course (same course code) to obtain a higher grade.",
    "Retaking a course (not improvement) means re-registering a failed course.",
    "For improvement retakes, use the highest score if ≥ 4.0; if any attempt fails, deduct 0.3 points per credit from the course’s grade points.",
    "A failed course (score < 4.0) contributes no credits.",
    "Improvement retakes do not change accumulated credits.",
    "A student has a GPA of 7.4 with 60 credits, including two courses: C1 (4 credits, original grade 6.8), C2 (3 credits, original grade 5.5).",
    "For C1, the student retook for improvement three times, scoring 7.2, 3.5 (failed), 6.0.",
    "For C2, the student retook for improvement twice, scoring 6.5, 7.0.",
    "After C1’s failure, the student retook C1 (as a failed course) and scored 5.8.",
    "The student took a new course, C3 (5 credits, scored 8.0)."
],
"questions": [
    "What are the final grades used for GPA in the student’s retaken courses (C1, C2)?",
    "What is the student’s updated GPA after all course attempts?"
]}
Output:
{"answers": [
    "7.2, 7.0", "7.52"
],
"idx": [
    [3, 6, 7, 8],
    [3, 5, 6, 7, 8, 10]
],
"explanation": [
    "Premise 6 states the student had a 4-credit course C1 with an original grade of 6.8 and a 3-credit course C2 with 5.5. Premise 7 says C1 was retaken for improvement three times, scoring 7.2, 3.5 (failed), and 6.0. Premise 8 says C2 was retaken twice, scoring 6.5 and 7.0. Premise 3 says for improvement retakes, use the highest score if ≥ 4.0, with a 0.3-point penalty per credit if any attempt failed. For C1, Max(6.8, 7.2, 3.5, 6.0) = 7.2, with a failure, but the score remains 7.2 (penalty affects grade points). For C2, Max(5.5, 6.5, 7.0) = 7.0, no failure, so score is 7.0. Final grades: 7.2 for C1, 7.0 for C2.",
    "Premise 6 gives a GPA of 7.4 over 60 credits, so grade points are 7.4 × 60 = 444, with C1 (4 credits, 6.8, points 27.2) and C2 (3 credits, 5.5, points 16.5), leaving 53 credits at 400.3 points. Premise 7 says C1 retakes scored 7.2, 3.5 (failed), 6.0; Premise 3 uses Max(6.8, 7.2, 3.5, 6.0) = 7.2, penalty 0.3 × 4 = 1.2 for failure, so points = 7.2 × 4 − 1.2 = 27.6, change = 27.6 − 27.2 = 0.4. Premise 8 says C2 retakes scored 6.5, 7.0; Max(5.5, 6.5, 7.0) = 7.0, no penalty, points = 7.0 × 3 = 21.0, change = 21.0 − 16.5 = 4.5. Premise 10 adds C3 (5 credits, 8.0, points 40). Total grade points: 400.3 + 27.6 + 21.0 + 40 = 488.9. Total credits (Premise 5): 60 + 5 = 65. GPA = 488.9 / 65 ≈ 7.5215, rounded to 7.52."
]}


"""
    if (useRetrieval):
        tmp = get_closest_strings(json.dumps(input_data), 3)
        if (len(tmp) > 0):
            BONUS_STRING = "THIS IS SOME DATASET RELATED TO (YOU CAN USE IS ANSWER TOO):\n"
            for idx, string in enumerate(tmp):
                BONUS_STRING += f"DATA {idx+1}: "
                BONUS_STRING += string + "\n"
            
            examples = BONUS_STRING + examples

    def build_prompt(premises, question, start_time):
        formatted_premises = "\n".join([f"{i+1}. {p}" for i, p in enumerate(premises)])
        prompt = (
            f"{system_prompt}\n\n"
            f"Premises:\n{formatted_premises}\n\n"
            f"Question:\n{question}\n\n"
            "Instructions:\n"
            "- Select the best answer choice (or 'True'/'False' or number if applicable ).\n"
            "- List indices of relevant premises.\n"
            "- Write a detailed logical explanation.\n"
            "- Always double-check for logical consistency before deciding.\n\n"
            "Output JSON format:\n"
            "{\n"
            "\"answer\": <answer choice>, \n"
            "\"idx\": [list of relevant premise indices],\n"
            "\"explanation\": <step-by-step explanation>\n"
            "}\n"
        )
        return prompt

    outputs = {
        "answers": [],
        "idx": [],
        "explanation": []
    }

    for question in questions:
        prompt = build_prompt(premises, question, start_time)

        retries = 1
        while retries > 0:
            try:
                # print('system_prompt:',system_prompt)
                # print('prompt:',prompt)
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\n\n" + examples},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    timeout=remaining_time(start_time),
                )
                content = response.choices[0].message.content
                # print("```",content,"```")
                # Try to safely parse
                parsed = to_json(content)
                # print('parsed:', parsed)

                outputs["answers"].append(parsed["answer"])
                outputs["idx"].append(parsed["idx"])
                outputs["explanation"].append(parsed["explanation"])
                break
            except Exception as e:
                print(f"Error: {e}")
                retries -= 1
                if (retries==0):
                    outputs["answers"].append("Yes")
                    outputs["idx"].append([])
                    outputs["explanation"].append("")

    return outputs

# Example usage:

if __name__ == "__main__":
    example_input = {
        "premises-NL": [
            "Ebbinghaus' forgetting curve formula: R = e^(-t/S), where R is retention rate, t is elapsed time, and S is review interval.",
            "A learning algorithm based on spaced repetition can adjust review intervals based on individual proficiency.",
            "Adequate sleep enhances memory consolidation after each review session.",
            "Creating flashcards with concise questions improves retention compared to passive reading.",
            "Reviewing just before forgetting significantly boosts memory efficiency.",
            "Neuroscience studies show self-testing activates the hippocampus, enhancing information recall.",
            "Encountering knowledge in various contexts improves retention compared to monotonous repetition.",
            "Too short review intervals reduce retention due to lack of time for consolidation.",
            "Too long review intervals risk forgetting most of the material before review.",
            "AI can personalize study schedules, optimizing memory retention for each student based on their progress."
        ],
        "questions": [
            "Based on the learning science principles, which statement is correct?\nA. Spaced repetition improves both memory and academic performance\nB. Excessively long intervals preserve knowledge without review\nC. AI cannot optimize study schedules for memory retention\nD. Passive reading is more effective than active recall",
            "Which of these conclusions is supported by the forgetting curve research?\nA. Review timing has no impact on retention\nB. Optimal intervals prevent both premature review and excessive forgetting\nC. Sleep has no effect on memory consolidation\nD. All learning methods yield identical results",
            "Does spaced repetition improves both memory and academic performance?"
        ]
    }
    

    # result = solve_fol_problem_fullLM(example_input["premises-NL"], example_input["questions"][0], 0)
    result = solve_fol_problem_(example_input)
    print(json.dumps(result, indent=4))