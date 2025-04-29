from z3 import *
import re
import uuid
import copy
from z3_parser import string_to_z3_formula

set_param(proof=True)

def solve_fol(inputs, conclusions):
    for idx, conclusion in enumerate(conclusions):
        ss0 = Solver()
        ss1 = Solver()
        for idx, premise in enumerate(inputs):
            # print('premise:',premise)
            formular = string_to_z3_formula(premise)
            ss0.assert_and_track(formular, f"idx-{idx+1}")
            ss1.assert_and_track(formular, f"idx-{idx+1}")
        formular = string_to_z3_formula(conclusion)
        ss1.assert_and_track(Not(formular), 'goal')
        ss0.assert_and_track(formular, 'goal')
        ans = "No concluse"
        idx = []
        proof = ""
        if ss0.check() == unsat:
            print(f"Conclusion: {conclusion} is false")
            print("Used premises (unsat core):", ss0.unsat_core())
            # print("\nProof:")
            # print(ss0.proof())
            ans = "false"
            idx = str(ss0.unsat_core())
            proof = str(ss0.proof())
        elif ss1.check() == unsat:
            print(f"Conclusion: {conclusion} is true")
            print("Used premises (unsat core):", ss1.unsat_core())
            ans = "true"
            idx = str(ss1.unsat_core())
            proof = str(ss1.proof())
        else:
            print("No concluse")
        if (len(idx)!=0):
            idx = str(idx)[1:-1]
            idx = idx.split(',')
            idx = [int(x.strip()[4:]) if x.strip().startswith('idx-') else x.strip() for x in idx]
            if ('goal' in idx): idx.remove('goal')
        # print('ans:',ans)
        # print('idx:',idx)
        return ans, idx, proof 
    


if __name__ == "__main__":
    # inputs =[
    #     "ForAll(x, complete(x, A) → enroll(x, B))",
    #     "ForAll(x, (enroll(x, B) ∧ pass(x, B)) → enroll(x, C))",
    #     "ForAll(x, enroll(x, C) → eligible_internship(x))",
    #     "complete(david, A)",
    #     "enroll(david, B) ∧ pass(david, B)"
    # ]
    # solve_fol(inputs, ["use_equipment(Alex) ∧ has_trainer(Alex)","¬eligible_internship(david)"])
    # inputs = [
    #     "ForAll(x, ForAll(h, (clinical_hours(x, h) ≥ 500) → advanced_practice(x)))",
    #     "clinical_hours(john, 600)",
    #     "registered_nurse(john)",
    #     "ForAll(x, (registered_nurse(x) ∧ advanced_practice(x)) → can_prescribe(x))"
    # ]

    inputs = [
		"ForAll(s, (study(s,PoliticalTheory) > 12) → understand(s,PoliticalIdeologies))",
        "ForAll(s, understand(s,PoliticalIdeologies) → analyze(s,GovernmentPolicies))",
        "ForAll(s, analyze(s,GovernmentPolicies) → (debate(s) ∨ write_essay(s)))",
        "ForAll(s, ¬debate(s) → write_essay(s))",
        "ForAll(s, (study(s,PoliticalTheory) < 6) → struggle(s,PoliticalIdeologies))",
        "ForAll(s, professor_requires(s,Debate) → (debate(s) ∨ justified_reason(s)))",
        "ForAll(s, (write_essay(s) ∧ high_quality(s)) → academic_recognition(s))",
        "ForAll(s, (academic_recognition(s) ∧ field(s,PoliticalStudies)) → qualify_fellowship(s))",
        "ForAll(p, controversial(p) → ForAll(s, must_analyze(s,p)))",
        "ForAll(s, (¬debate(s) ∧ ¬write_essay(s)) → fail(s,PoliticalTheory))",
        "ForAll(p, (academic_recognition(s) ∧ field(s,PoliticalStudies)) → ¬qualify_fellowship(s))"
	]
    solve_fol(inputs, ["academic_recognition(s) ∧ field(s,PoliticalStudies)", "book_training(Alex)","¬eligible_internship(david)"])