from z3 import *
import re
import uuid

def is_bracket_correct(s):
    stack = []
    for char in s:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return not stack

def string_to_z3_formula(input_str):
    # Dictionary to store sorts dynamically
    sorts = {}
    variables = {}
    constants = {}
    functions = {}
    
    def get_or_create_sort(sort_name):
        """Get or create a Z3 sort by name."""
        if sort_name == 'Int':
            return IntSort()
        if sort_name not in sorts:
            sorts[sort_name] = DeclareSort(sort_name)
        return sorts[sort_name]
    
    def declare_variable(var_name, sort_name='Generic'):
        """Declare a new Z3 variable with a given sort."""
        sort = get_or_create_sort(sort_name)
        if var_name not in variables:
            variables[var_name] = Const(var_name, sort)
        return variables[var_name]
    
    def declare_constant(const_name, sort_name='Generic'):
        """Declare a new Z3 constant with a given sort."""
        sort = get_or_create_sort(sort_name)
        if const_name not in constants:
            constants[const_name] = Const(const_name, sort)
        return constants[const_name]
    
    def declare_function(pred_name, arg_sorts, return_sort=BoolSort()):
        """Declare a Z3 function with given argument sorts and return sort."""
        key = (pred_name, tuple(arg_sorts), return_sort)
        if key not in functions:
            functions[key] = Function(pred_name, *[s for s in arg_sorts] + [return_sort])
        return functions[key]
    
    def find_top_level_split(expr, operators):
        """Find the top-level occurrence of any operator, respecting parentheses and quantifiers."""
        paren_count = 0
        i = 0
        while i < len(expr):
            char = expr[i]
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif paren_count == 0:
                for op in operators:
                    if expr[i:i+len(op)] == op:
                        # Ensure the operator is at the top level by checking context
                        # Verify that the left and right sides form valid expressions
                        left_part = expr[:i].strip()
                        right_part = expr[i+len(op):].strip()
                        # Basic check to ensure left_part is a complete expression
                        if left_part.startswith('ForAll') or left_part.startswith('Exists'):
                            # Check if left_part is a complete quantifier expression
                            if left_part.endswith(')') and paren_count == 0:
                                return i, op
                        elif left_part and right_part:
                            return i, op
            i += 1
        return None
    
    def parse_expression(expr, bound_vars, sort_hints=None):
        """Recursively parse a logical expression into a Z3 formula with operator precedence."""
        expr = expr.strip()
        if sort_hints is None:
            sort_hints = {}
        
        # Remove outer parentheses if they wrap the entire expression
        if expr.startswith('(') and expr.endswith(')'):
            paren_count = 0
            valid = True
            for i, char in enumerate(expr):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                if paren_count == 0 and i < len(expr) - 1:
                    valid = False
                    break
            if valid and paren_count == 0:
                return parse_expression(expr[1:-1], bound_vars, sort_hints)
        
        # Handle quantifiers (ForAll, Exists)
        quantifier_match = re.match(r'^(ForAll|Exists)\s*\(\s*(\w+)\s*,\s*(.+)\)$', expr)
        if quantifier_match:
            quant_type, var, body = quantifier_match.groups()
            if is_bracket_correct(body):
                # Infer IntSort for variables used in comparisons
                sort_name = 'Int' if re.search(rf'\b{var}\b\s*[≥≤=<>]', body) else sort_hints.get(var, 'Generic')
                var_const = declare_variable(var, sort_name)
                new_bound_vars = bound_vars | {var}
                body_expr = parse_expression(body, new_bound_vars, sort_hints)
                if quant_type == 'ForAll':
                    return ForAll(var_const, body_expr)
                else:
                    return Exists(var_const, body_expr)
        
        # Handle operators by precedence
        # Lowest precedence: Biconditional (↔)
        split = find_top_level_split(expr, ['↔'])
        if split:
            idx, operator = split
            left = parse_expression(expr[:idx], bound_vars, sort_hints)
            right = parse_expression(expr[idx+len(operator):], bound_vars, sort_hints)
            return left == right
        
        # Implication (→)
        split = find_top_level_split(expr, ['→'])
        if split:
            idx, operator = split
            left = parse_expression(expr[:idx], bound_vars, sort_hints)
            right = parse_expression(expr[idx+len(operator):], bound_vars, sort_hints)
            return Implies(left, right)
        
        # Disjunction (∨)
        split = find_top_level_split(expr, ['∨'])
        if split:
            idx, operator = split
            left = parse_expression(expr[:idx], bound_vars, sort_hints)
            right = parse_expression(expr[idx+len(operator):], bound_vars, sort_hints)
            return Or(left, right)
        
        # Conjunction (∧)
        split = find_top_level_split(expr, ['∧'])
        if split:
            idx, operator = split
            left = parse_expression(expr[:idx], bound_vars, sort_hints)
            right = parse_expression(expr[idx+len(operator):], bound_vars, sort_hints)
            return And(left, right)
        
        # Negation (¬)
        if expr.startswith('¬'):
            sub_expr = parse_expression(expr[1:], bound_vars, sort_hints)
            return Not(sub_expr)
        
        # Comparison operators (≥, ≤, =, <, >)
        for op in ['≥', '≤', '=', '<', '>']:
            split = find_top_level_split(expr, [op])
            if split:
                idx, operator = split
                left = parse_expression(expr[:idx], bound_vars, sort_hints)
                right = parse_expression(expr[idx+len(operator):], bound_vars, sort_hints)
                if left.sort() != IntSort() or right.sort() != IntSort():
                    raise ValueError(f"Comparison {operator} requires integer arguments, got {left.sort()} and {right.sort()}")
                if operator == '≥':
                    return left >= right
                elif operator == '≤':
                    return left <= right
                elif operator == '=':
                    return left == right
                elif operator == '<':
                    return left < right
                elif operator == '>':
                    return left > right
        
        # Handle predicates or functions (e.g., P(x), clinical_hours(x, h))
        pred_match = re.match(r'^(\w+)\s*\(\s*([\w\s,]+)\s*\)$', expr)
        if pred_match:
            pred_name, args_str = pred_match.groups()
            args = [arg.strip() for arg in args_str.split(',')]
            
            # Determine sorts for arguments
            arg_sorts = []
            processed_args = []
            for arg in args:
                if arg in bound_vars:
                    var = variables[arg]
                    arg_sorts.append(var.sort())
                    processed_args.append(var)
                else:
                    sort_name = sort_hints.get(arg, 'Generic')
                    if arg.isupper() or arg in ['True', 'False']:
                        const = declare_constant(arg, sort_name)
                        arg_sorts.append(const.sort())
                        processed_args.append(const)
                    elif re.match(r'^\d+$', arg):  # Handle numerical constants
                        processed_args.append(IntVal(int(arg)))
                        arg_sorts.append(IntSort())
                    else:
                        # Infer IntSort for variables in comparisons
                        sort_name = 'Int' if re.search(rf'\b{arg}\b\s*[≥≤=<>]', input_str) else sort_hints.get(arg, 'Generic')
                        var = declare_variable(arg, sort_name)
                        arg_sorts.append(var.sort())
                        processed_args.append(var)
            
            # Infer return sort: Int if used in a comparison, else Bool
            escaped_pred_name = re.escape(pred_name)
            func_pattern = rf'{escaped_pred_name}\s*\({args_str}\)\s*[≥≤=<>]'
            return_sort = IntSort() if re.search(func_pattern, input_str) else BoolSort()
            
            func = declare_function(pred_name, arg_sorts, return_sort)
            return func(*processed_args)
        
        # Handle numerical constants
        if re.match(r'^\d+$', expr):
            return IntVal(int(expr))
        
        # Handle boolean constants
        if expr == 'True':
            return BoolVal(True)
        if expr == 'False':
            return BoolVal(False)
        
        # Handle standalone variables or constants
        if re.match(r'^\w+$', expr):
            if expr in bound_vars:
                return variables[expr]
            # Infer IntSort for variables in comparisons
            sort_name = 'Int' if re.search(rf'\b{expr}\b\s*[≥≤=<>]', input_str) else sort_hints.get(expr, 'Generic')
            if expr.isupper():
                return declare_constant(expr, sort_name)
            return declare_variable(expr, sort_name)
        
        raise ValueError(f"Unable to parse expression: {expr}")
    
    try:
        sort_hints = {}  # Example: {'x': 'Person', 'h': 'Int'}
        formula = parse_expression(input_str, set(), sort_hints)
        return formula
    except Exception as e:
        raise ValueError(f"Error parsing logical string: {str(e)}")