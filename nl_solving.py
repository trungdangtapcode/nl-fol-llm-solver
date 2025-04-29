import re
import json
from nl_to_fol import nl_to_fol
from order_correcting import permute_fol
from bracket_correcting import fix_nested_fol_brackets
from z3_solve import solve_fol
from simple_solve import solve_fol_problem_fullLM

def extract_choices(text):
    # Find all options starting with A., B., C., D.
    matches = re.findall(r'[A-D]\.\s(.*?)(?=\s[A-D]\.|$)', text)
    if len(matches) == 4:
        return [choice.strip() for choice in matches]
    else:
        return None


def solving_fol_single_question(premises_nl, question, reOrder = True):
    fol_formulas = nl_to_fol(premises_nl, question)
    # print('fol_formulas:',fol_formulas)
    premises_fol = fol_formulas["premise"]
    if (reOrder):
        premises_fol = permute_fol(premises_nl, premises_fol)
    conclusion = fol_formulas["question"]
    conclusions = fix_nested_fol_brackets([conclusion])
    # print('conclusion:',conclusion)
    ans, idx, proof = solve_fol(premises_fol, conclusions)
    # print(ans, idx, proof)
    proof = " ".join(proof.split())
    if (len(proof)>500): proof = proof[:500]
    return ans, idx, proof

def solving_fol(inputs):
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
                    ans, idx, proof = solving_fol_single_question(premises_nl, question)
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
                ans, idx, proof = solving_fol_single_question(premises_nl, question)
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
            response = solve_fol_problem_fullLM(premises_nl, question)
            print('response:', response)
            res["answers"].append(response["answers"][0])
            res["idx"].append(response["idx"][0])
            res["explanation"].append(response["explanation"][0])

    for ans in res["idx"]:
        ans.sort()
    for i in range(len(res["explanation"])):
        x = res["explanation"][i]
        if isinstance(x, list):
            res["explanation"][i] = " ".join(x)
        
    return res


if __name__ == "__main__":
    premises_nl = [
		"Students who have completed the core curriculum and passed the science assessment are qualified for advanced courses.",
		"Students who are qualified for advanced courses and have completed research methodology are eligible for the international program.",
		"Students who have passed the language proficiency exam are eligible for the international program.",
		"Students who are eligible for the international program and have completed a capstone project are awarded an honors diploma.",
		"Students who have been awarded an honors diploma and have completed community service qualify for the university scholarship.",
		"Students who have been awarded an honors diploma and have received a faculty recommendation qualify for the university scholarship.",
		"Sophia has completed the core curriculum.",
		"Sophia has passed the science assessment.",
		"Sophia has completed the research methodology course.",
		"Sophia has completed her capstone project.",
		"Sophia has completed the required community service hours."
    ]
    questions = ["Does Sophia qualify for the university scholarship, according to the premises?"]
    inputs = {"premises-NL":premises_nl,"questions":questions}
    print(inputs)
    result = solving_fol(inputs)

    # result = solve_fol_problem_fullLM(example_input["premises-NL"], example_input["questions"][0])
    # result = solve_fol_problem_(example_input)
    # print(json.dumps(result, indent=4))