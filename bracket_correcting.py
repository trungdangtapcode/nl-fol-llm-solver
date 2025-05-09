from openai_clients import *

def is_bracket_correct(statement):
    """
    Check if a FOL statement has balanced parentheses.
    Args:
        statement (str): The FOL statement to check.
    Returns:
        bool: True if balanced, False otherwise.
    """
    stack = []
    for char in statement:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0

def fix_nested_fol_brackets(fol_statements, start_time):
    """
    Fix only incorrect bracket nesting in a list of FOL statements using OpenAI API.
    Args:
        fol_statements (list of str): List of FOL expressions to correct.
    Returns:
        list of str: Corrected FOL expressions with proper brackets, preserving original ones if already correct.
    """

    # Identify which need fixing
    to_fix_indices = []
    to_fix_statements = []
    for idx, stmt in enumerate(fol_statements):
        if not is_bracket_correct(stmt):
            to_fix_indices.append(idx)
            to_fix_statements.append(stmt)
    if (len(to_fix_statements)==0):
        return fol_statements
    
    prompt = f"""You are an expert in First-Order Logic (FOL) syntax.
Given a list of FOL statements with potentially incorrect or missing parentheses, 
your task is to fix only the parentheses to make each statement logically correct, 
without changing any meaning or structure other than fixing brackets.
Always ensure that operators (like ∧, ∨, →) are properly enclosed. 
Then add parentheses where needed to correctly group logical operators (∧, ∨) and comparison operators (=, ≥, ≤, >, <).

Example:
Input:
[
"ForAll(x, (valid_membership(x) ∧ safety_orientation(x) → use_equipment(x))",
"ForAll(x, (receive_update_email(x) → registered(x))",
"ForAll(a, ForAll(b, ForAll(c, prereq(a, b) ∧ prereq(b, c)) → prereq(a, c)))",
"ForAll(x, (active_status(x) ∧ completed_courses(x) ≥ 5) → eligible_for_advanced_classes(x))"
]

Output:
[
"ForAll(x, (valid_membership(x) ∧ safety_orientation(x)) → use_equipment(x))",
"ForAll(x, (receive_update_email(x) → registered(x)))",
"ForAll(a, ForAll(b, ForAll(c, (prereq(a, b) ∧ prereq(b, c)) → prereq(a, c))))",
"ForAll(x, (active_status(x) ∧ (completed_courses(x) ≥ 5)) → eligible_for_advanced_classes(x))"
]

Now fix the following FOL expressions:
{fol_statements}

Return ONLY the fixed list as a Python list of strings, no explanation."""

    response = client.chat.completions.create(
        model=model_name,  # qwen2.5-coder
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    def format_output(text):
        if (text.startswith('```python')): text = text[9:-3]
        return text

    # Get the text output
    fixed_list_text = response.choices[0].message.content.strip()
    fixed_list_text = format_output(fixed_list_text)
    # print(fixed_list_text)
    # print('fixed_list_text:',fixed_list_text)
    try:
        # Safely evaluate the output to a Python list
        fixed_statements = eval(fixed_list_text)
        if not isinstance(fol_statements, list):
            raise ValueError("Output is not a list.")
    except Exception as e:
        raise ValueError(f"Failed to parse model output: {e}")

    output = []
    fixed_idx = 0
    for idx in range(len(fol_statements)):
        if idx in to_fix_indices:
            output.append(fixed_statements[fixed_idx])
            fixed_idx += 1
        else:
            output.append(fol_statements[idx])

    return output

# Example usage
if __name__ == "__main__":
    input_fol = [
        "ForAll(x, (valid_membership(x) ∧ safety_orientation(x) → use_equipment(x))",
        "ForAll(x, (receive_update_email(x) → registered(x))",
        "ForAll(a, ForAll(b, ForAll(c, prereq(a, b) ∧ prereq(b, c)) → prereq(a, c)))",
        "ForAll(x, UpdateEmail(x) → Paid(x))",
        "ForAll(x, (active_status(x) ∧ completed_courses(x) ≥ 1) → eligible_for_advanced_classes(x))"
    ]
    corrected_fol = fix_nested_fol_brackets(input_fol)
    print(corrected_fol)
