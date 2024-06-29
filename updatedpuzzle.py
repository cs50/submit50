from logic import *

# Symbols for characters A, B, C
AKnight = Symbol("A is a Knight")
AKnave = Symbol("A is a Knave")

BKnight = Symbol("B is a Knight")
BKnave = Symbol("B is a Knave")

CKnight = Symbol("C is a Knight")
CKnave = Symbol("C is a Knave")

# Puzzle 0
# A says "I am both a knight and a knave."
knowledge0 = And(
    Imp(AKnight, AKnave),   # If A is a knight, A must be a knave
    Imp(AKnave, Not(AKnave))   # If A is a knave, A cannot be a knave (contradiction)
)

# Puzzle 1
# A says "We are both knaves."
# B says nothing.
knowledge1 = And(
    Biconditional(AKnight, And(AKnave, BKnave))   # A is a knight if and only if both are knaves
)

# Puzzle 2
# A says "We are the same kind."
# B says "We are of different kinds."
knowledge2 = And(
    Biconditional(AKnight, Or(And(AKnight, BKnight), And(AKnave, BKnave))),   # A is a knight if and only if they are both knights or both knaves
    Biconditional(BKnight, Or(And(AKnight, BKnave), And(AKnave, BKnight)))    # B is a knight if and only if they are of different kinds
)

# Puzzle 3
# A says either "I am a knight." or "I am a knave.", but you don’t know which.
# B says "A said ‘I am a knave.’"
# B then says “C is a knave.”
# C says “A is a knight.”
knowledge3 = And(
    Or(AKnight, AKnave),   # A is either a knight or a knave
    Biconditional(BKnight, Not(AKnight)),   # B is a knight if and only if A is a knave
    Biconditional(BKnave, CKnave),   # B is a knave if and only if C is a knave
    Biconditional(CKnight, AKnight)   # C is a knight if and only if A is a knight
)

def main():
    symbols = [AKnight, AKnave, BKnight, BKnave, CKnight, CKnave]
    puzzles = [
        ("Puzzle 0", knowledge0),
        ("Puzzle 1", knowledge1),
        ("Puzzle 2", knowledge2),
        ("Puzzle 3", knowledge3)
    ]
    for puzzle, knowledge in puzzles:
        print(puzzle)
        if len(knowledge.conjuncts) == 0:
            print("    Not yet implemented.")
        else:
            for symbol in symbols:
                if model_check(knowledge, symbol):
                    print(f"    {symbol}")


if __name__ == "__main__":
    main()
