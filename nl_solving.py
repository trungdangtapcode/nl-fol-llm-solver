import re
import json
from nl_to_fol import nl_to_fol
from openai_clients import step_change_client
from order_correcting import permute_fol
from bracket_correcting import fix_nested_fol_brackets
from z3_solve import solve_fol
from simple_solve import solve_fol_problem_fullLM
from timeout import *

def extract_choices(text):
    # Find all options starting with A., B., C., D.
    matches = re.findall(r'[A-D]\.\s(.*?)(?=\s[A-D]\.|$)', text)
    if len(matches) == 4:
        return [choice.strip() for choice in matches]
    else:
        return None


cache = {}

def solving_fol_single_question(premises_nl, question, start_time, reOrder = True, fixBracket = False):
    if (is_timeout(start_time)): 
        return TIMEOUT_RETURN
    fol_formulas = nl_to_fol(premises_nl, question, start_time)
    step_change_client()
    # print('fol_formulas:',fol_formulas)
    premises_fol = fol_formulas["premise"]
    if (reOrder and not is_timeout(start_time)):
        premises_fol = permute_fol(premises_nl, premises_fol, start_time)
        step_change_client()
    conclusion = fol_formulas["question"]
    if (fixBracket and not is_timeout(start_time)):
        conclusions = fix_nested_fol_brackets([conclusion], start_time)
        step_change_client()
    else:
        conclusions = [conclusion]
    # print('conclusion:',conclusion)
    ans, idx, proof = solve_fol(premises_fol, conclusions)
    # print(ans, idx, proof)
    proof = " ".join(proof.split())
    if (len(proof)>500): proof = proof[:500]
    return ans, idx, proof

def solving_fol(inputs, start_time):
    premises_nl = inputs["premises-NL"]
    questions = inputs["questions"]
    standerize_ans = {"true":"Yes", "false":"No", "No concluse": "No"}
    int_to_choice = ["A", "B", "C", "D"]
    res = {
        "answers":[],
        "idx":[],
        "explanation": []
    }
    for question in questions:
        doesError = False
        try:
            choices = extract_choices(question)
            trueChoice = []
            falseChoice = []
            noConcluseChoice = []
            if choices is not None:
                for choice_idx, choice in enumerate(choices):
                    ans, idx, proof = solving_fol_single_question(premises_nl, question, start_time, start_time)
                    if ans=='true':
                        trueChoice.append((int_to_choice[choice_idx], idx, proof))
                    elif ans=='false':
                        falseChoice.append((int_to_choice[choice_idx], idx, proof))
                    else:
                        noConcluseChoice.append((int_to_choice[choice_idx], idx, proof))
                if len(trueChoice)==1:
                    res["answers"].append(trueChoice[0][0])
                    res["idx"].append(trueChoice[0][1])
                    res["explanation"].append(trueChoice[0][2])
                elif len(falseChoice)==3 and len(noConcluseChoice)==1:
                    res["answers"].append(noConcluseChoice[0][0])
                    res["idx"].append(noConcluseChoice[0][1])
                    res["explanation"].append(noConcluseChoice[0][2])
                else:
                    doesError = True
            else:
                ans, idx, proof = solving_fol_single_question(premises_nl, question, start_time)
                if len(idx)==0:
                    doesError = True
                    idx = list(range(1,len(premises_nl)+1))
                else:
                    res["answers"].append(standerize_ans[ans])
                    res["idx"].append(idx)
                    res["explanation"].append(proof)
        except Exception as error:
            print("ERROR!!!!!!", error)
            doesError = True
        if doesError:
            response = solve_fol_problem_fullLM(premises_nl, question, start_time) # took long
            step_change_client()
            print('response:', response)
            res["answers"].append(response["answers"][0])
            res["idx"].append(response["idx"][0])
            res["explanation"].append(response["explanation"][0])

    for ans in res["idx"]:
        print('ans:', ans)
        ans.sort()
    for i in range(len(res["explanation"])):
        x = res["explanation"][i]
        if isinstance(x, list):
            res["explanation"][i] = " ".join(x)
        
    return res


if __name__ == "__main__":
    # premises_nl = [
	# 	"Students who have completed the core curriculum and passed the science assessment are qualified for advanced courses.",
	# 	"Students who are qualified for advanced courses and have completed research methodology are eligible for the international program.",
	# 	"Students who have passed the language proficiency exam are eligible for the international program.",
	# 	"Students who are eligible for the international program and have completed a capstone project are awarded an honors diploma.",
	# 	"Students who have been awarded an honors diploma and have completed community service qualify for the university scholarship.",
	# 	"Students who have been awarded an honors diploma and have received a faculty recommendation qualify for the university scholarship.",
	# 	"Sophia has completed the core curriculum.",
	# 	"Sophia has passed the science assessment.",
	# 	"Sophia has completed the research methodology course.",
	# 	"Sophia has completed her capstone project.",
	# 	"Sophia has completed the required community service hours."
    # ]
    # questions = ["Does Sophia qualify for the university scholarship, according to the premises?"]
    # inputs = {"premises-NL":premises_nl,"questions":questions}
    # print(inputs)

    inputs = {
        "premises-NL": [
            "Thesis eligibility requires ≥ 100 credits, GPA ≥ 5.5 (scale 0–10), capstone completion, and ≥ 80 capstone hours.",
            "Capstone completion requires ≥ 80 credits and a 5-credit capstone course (grade ≥ 4.0).",
            "Failed courses (grade < 4.0) add 0 credits, 0 capstone hours.",
            "Improvement retakes (grade ≥ 4.0) use highest grade, no extra credits/hours.",
            "Each course (grade ≥ 4.0) adds capstone hours: 3 credits = 6 hours, 4 credits = 8 hours, 5 credits = 10 hours.",
            "Final-year students (Year 4) with capstone but < 80 hours can join capstone workshops (15 hours), if GPA ≥ 5.0.",
            "A student (Year 3) has a GPA of 5.8, 85 credits, 100 capstone hours, no capstone course, including C1 (3 credits, 6.0, 6 hours), C2 (4 credits, 5.5, 8 hours).",
            "The student took capstone course C3 (5 credits, 4.5), retook C1 (6.5), took C4 (3 credits, 3.8, failed), joined 2 workshops."
        ],
        "questions": [
            "What is the student’s updated GPA after all course attempts?",
            "How many capstone hours has the student accumulated, and are they eligible for the thesis?"
        ]
    }

    result = solving_fol(inputs)
    print('RESULT:', result)

    # result = solve_fol_problem_fullLM(example_input["premises-NL"], example_input["questions"][0], 0)
    # result = solve_fol_problem_(example_input)
    # print(json.dumps(result, indent=4))