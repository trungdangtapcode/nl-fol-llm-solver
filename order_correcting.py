import re
from openai_clients import *

def clean_output_order(content):
    """
    Cleans and extracts list of (NL-index, FOL-index) pairs from model output.
    """
    # Find the first list pattern like [(0,1), (1,0), ...]
    match = re.search(r'\[\s*(\(\s*\d+\s*,\s*\d+\s*\)\s*,?\s*)+\]', content)
    if match:
        cleaned = match.group(0)
        return eval(cleaned)
    else:
        raise ValueError(f"Could not find a valid list in model output: {content}")

def match_fol_nl(nl_premises, fol_premises):
    """
    Matches NL and FOL premises using an LLM and returns a list of (NL-index, FOL-index).
    """

    system_prompt = """You are an expert in formal logic and natural language understanding.
Given a list of Natural Language (NL) premises and First Order Logic (FOL) premises, your task is to match them correctly.
Each NL premise should correspond to one FOL premise, ensuring logical consistency.

First, study this example carefully:

Example Input:
"NL-premises": [
    "Alex has completed safety orientation.",
    "Alex has a membership duration of 8 months.",
    "Alex has paid annual fees on time.",
    "If a person has a valid membership card and has completed safety orientation, they can use equipment.",
    "If a person can use equipment and has a trainer, they can book training.",
    "If a person’s membership duration is at least 6 months, they are eligible for a trainer.",
    "If a person has paid the annual fee, they have a valid membership."
],
"FOL-premises": [
    "membership_duration(Alex) = 8",
    "safety_orientation(Alex)",
    "ForAll(x, (valid_membership(x) ∧ safety_orientation(x)) → use_equipment(x))",
    "paid_annual_fee(Alex)",
    "ForAll(x, paid_annual_fee(x) → valid_membership(x))",
    "ForAll(x, (use_equipment(x) ∧ has_trainer(x)) → book_training(x))",
    "ForAll(x, (membership_duration(x) ≥ 6) → eligible_trainer(x))",
]
Example Output:
[(0,1), (1,0), (2,3), (3,2), (4,5), (5,6), (6,4)]

You must produce the output in the exact same format, only returning the list of (NL-index, FOL-index) pairs.

Think carefully about the meaning behind each statement before matching."""

    user_prompt = f"""Now, here is a new matching task:

Natural Language Premises:
{[f"{i}: {nl}" for i, nl in enumerate(nl_premises)]}

FOL Premises:
{[f"{i}: {fol}" for i, fol in enumerate(fol_premises)]}

Return only the list of (NL-index, FOL-index) pairs:"""

    response = client.chat.completions.create(
        model=model_name, #"qwen2.5-coder" 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    
    try:
        matches = clean_output_order(content)
    except Exception as e:
        raise ValueError(f"Failed to parse model output: {content}") from e

    return matches


def permute_list(lst_b, pairs):
    # Create a result list with same size
    result = [None] * len(lst_b)
    for src, dest in pairs:
        result[src] = lst_b[dest]
    return result

def permute_fol(nl_premises, fol_premises):
    matches = match_fol_nl(nl_premises, fol_premises)
    fol_premises = permute_list(fol_premises, matches)
    return fol_premises

# Example usage
if __name__ == "__main__":
    nl_premises = [
        "Students with active status who have completed at least 5 courses are eligible for advanced classes.",
        "Eligible students must obtain advisor approval to take advanced classes.",
        "Sarah has active student status.",
        "Sarah has completed 4 courses.",
        "Sarah has obtained advisor approval."
    ]
    fol_premises = [
        "active_status(sarah)",
        "completed_courses(sarah) = 4",
        "has_approval(sarah)",
        "ForAll(x, (active_status(x) ∧ completed_courses(x) ≥ 5) → eligible_advanced(x))",
        "ForAll(x, eligible_advanced(x) → requires_approval(x))"
    ]

    fol_premises = permute_fol(nl_premises, fol_premises)
    # matches = match_fol_nl(nl_premises, fol_premises)
    # fol_premises = permute_list(fol_premises, matches)
    # print(matches)
    # print(fol_premises)
    for a, b in zip(nl_premises, fol_premises):
        print(a,'->',b)
