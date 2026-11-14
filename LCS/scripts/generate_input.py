import os
import argparse
import random

# caminhos
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "inputs"))
small_dir = os.path.join(base_dir, "small")
big_dir = os.path.join(base_dir, "big")
giga_dir = os.path.join(base_dir, "giga")

# estica a sequencia para ter o tamanho
def build_sequence(pattern, length):
    repetitions = (length // len(pattern)) + 1
    return (pattern * repetitions)[:length]

# salva os arquivos fileA e fileB na pasta inputs
def save_input_pair(target_dir, name, len_a, len_b, pattern_a, pattern_b, overwrite=True):
    case_dir = os.path.join(target_dir, name)
    os.makedirs(case_dir, exist_ok=True)
    
    file_a = os.path.join(case_dir, "fileA.in")
    file_b = os.path.join(case_dir, "fileB.in")
    
    if overwrite or not os.path.exists(file_a):
        with open(file_a, "w") as f:
            f.write(build_sequence(pattern_a, len_a) + "\n")
            
    if overwrite or not os.path.exists(file_b):
        with open(file_b, "w") as f:
            f.write(build_sequence(pattern_b, len_b) + "\n")
            
    print(f"Input gerado: {name}: sizeA={len_a}, sizeB={len_b}, patA='{pattern_a}', patB='{pattern_b}'")


if __name__ == "__main__":

    # padrão pseudoaletório, score esperado ~ min(N,M)/2
    random.seed(67)
    random_pattern_a = "".join(random.choices("01", k=32))
    random_pattern_b = "".join(random.choices("01", k=32))

    # padrões pré definidos que eu sei o quanto o score tem que dar
    # padrão 1 score tem que ser min(N,M) - 1
    pattern_1_a = "abcd"
    pattern_1_b = "bcda"

    # padrão 2 score tem que ser 0
    pattern_2_a = "a"
    pattern_2_b = "b"

    # padrão 3 score tem que ser min(N,M)/4
    pattern_3_a = "abcd"
    pattern_3_b = "defg"

    # padrão 4 score tem que ser min(N,M)
    pattern_4_a = "triviall"
    pattern_4_b = "triviall"

    # enunciado e caso com tamanho quebrado 
    save_input_pair(small_dir, "enunciado", 10, 7, "heagawghee", "pawheae")
    save_input_pair(small_dir, "numero_quebrado", 827, 827, pattern_1_a, pattern_1_b) 

    # quadrados 
    # Q1 small
    q1_dir = os.path.join(small_dir, "Q1")
    save_input_pair(q1_dir, "Q1_p1", 1000, 1000, pattern_1_a, pattern_1_b)
    save_input_pair(q1_dir, "Q1_p2", 1000, 1000, pattern_2_a, pattern_2_b)
    save_input_pair(q1_dir, "Q1_p3", 1000, 1000, pattern_3_a, pattern_3_b)
    save_input_pair(q1_dir, "Q1_p4", 1000, 1000, pattern_4_a, pattern_4_b)
    save_input_pair(q1_dir, "Q1_random", 1000, 1000, random_pattern_a, random_pattern_b)

    # Q2 small
    q2_dir = os.path.join(small_dir, "Q2")
    save_input_pair(q2_dir, "Q2_p1", 10000, 10000, pattern_1_a, pattern_1_b)
    save_input_pair(q2_dir, "Q2_p2", 10000, 10000, pattern_2_a, pattern_2_b)
    save_input_pair(q2_dir, "Q2_p3", 10000, 10000, pattern_3_a, pattern_3_b)
    save_input_pair(q2_dir, "Q2_p4", 10000, 10000, pattern_4_a, pattern_4_b)
    save_input_pair(q2_dir, "Q2_random", 10000, 10000, random_pattern_a, random_pattern_b)

    # Q3 small
    q3_dir = os.path.join(small_dir, "Q3")
    save_input_pair(q3_dir, "Q3_p1", 20000, 20000, pattern_1_a, pattern_1_b)
    save_input_pair(q3_dir, "Q3_p2", 20000, 20000, pattern_2_a, pattern_2_b)
    save_input_pair(q3_dir, "Q3_p3", 20000, 20000, pattern_3_a, pattern_3_b)
    save_input_pair(q3_dir, "Q3_p4", 20000, 20000, pattern_4_a, pattern_4_b)
    save_input_pair(q3_dir, "Q3_random", 20000, 20000, random_pattern_a, random_pattern_b)

    # Q4 small
    q4_dir = os.path.join(small_dir, "Q4")
    save_input_pair(q4_dir, "Q4_p1", 40000, 40000, pattern_1_a, pattern_1_b)
    save_input_pair(q4_dir, "Q4_p2", 40000, 40000, pattern_2_a, pattern_2_b)
    save_input_pair(q4_dir, "Q4_p3", 40000, 40000, pattern_3_a, pattern_3_b)
    save_input_pair(q4_dir, "Q4_p4", 40000, 40000, pattern_4_a, pattern_4_b)
    save_input_pair(q4_dir, "Q4_random", 40000, 40000, random_pattern_a, random_pattern_b)

    # Q5 big
    q5_dir = os.path.join(big_dir, "Q5")
    save_input_pair(q5_dir, "Q5_p1", 80000, 80000, pattern_1_a, pattern_1_b)
    save_input_pair(q5_dir, "Q5_p2", 80000, 80000, pattern_2_a, pattern_2_b)
    save_input_pair(q5_dir, "Q5_p3", 80000, 80000, pattern_3_a, pattern_3_b)
    save_input_pair(q5_dir, "Q5_p4", 80000, 80000, pattern_4_a, pattern_4_b)
    save_input_pair(q5_dir, "Q5_random", 80000, 80000, random_pattern_a, random_pattern_b)

    # Q6 big limite da memória acho
    q6_dir = os.path.join(big_dir, "Q6")
    save_input_pair(q6_dir, "Q6_p1", 100000, 100000, pattern_1_a, pattern_1_b)
    save_input_pair(q6_dir, "Q6_p2", 100000, 100000, pattern_2_a, pattern_2_b)
    save_input_pair(q6_dir, "Q6_p3", 100000, 100000, pattern_3_a, pattern_3_b)
    save_input_pair(q6_dir, "Q6_p4", 100000, 100000, pattern_4_a, pattern_4_b)
    save_input_pair(q6_dir, "Q6_random", 100000, 100000, random_pattern_a, random_pattern_b)

    # retangulos 
    # R1 2:1 big (direto e invertido)
    r1_dir = os.path.join(big_dir, "R1")
    save_input_pair(r1_dir, "R1_p1", 80000, 40000, pattern_1_a, pattern_1_b)
    save_input_pair(r1_dir, "R1_p2", 80000, 40000, pattern_2_a, pattern_2_b)
    save_input_pair(r1_dir, "R1_p3", 80000, 40000, pattern_3_a, pattern_3_b)
    save_input_pair(r1_dir, "R1_p4", 80000, 40000, pattern_4_a, pattern_4_b)
    save_input_pair(r1_dir, "R1_random", 80000, 40000, random_pattern_a, random_pattern_b)

    save_input_pair(r1_dir, "R1_inv_p1", 40000, 80000, pattern_1_a, pattern_1_b)
    save_input_pair(r1_dir, "R1_inv_p2", 40000, 80000, pattern_2_a, pattern_2_b)
    save_input_pair(r1_dir, "R1_inv_p3", 40000, 80000, pattern_3_a, pattern_3_b)
    save_input_pair(r1_dir, "R1_inv_p4", 40000, 80000, pattern_4_a, pattern_4_b)
    save_input_pair(r1_dir, "R1_inv_random", 40000, 80000, random_pattern_a, random_pattern_b)

    # R2 4:1 big (direto e invertido)
    r2_dir = os.path.join(big_dir, "R2")
    save_input_pair(r2_dir, "R2_p1", 80000, 20000, pattern_1_a, pattern_1_b)
    save_input_pair(r2_dir, "R2_p2", 80000, 20000, pattern_2_a, pattern_2_b)
    save_input_pair(r2_dir, "R2_p3", 80000, 20000, pattern_3_a, pattern_3_b)
    save_input_pair(r2_dir, "R2_p4", 80000, 20000, pattern_4_a, pattern_4_b)
    save_input_pair(r2_dir, "R2_random", 80000, 20000, random_pattern_a, random_pattern_b)

    save_input_pair(r2_dir, "R2_inv_p1", 20000, 80000, pattern_1_a, pattern_1_b)
    save_input_pair(r2_dir, "R2_inv_p2", 20000, 80000, pattern_2_a, pattern_2_b)
    save_input_pair(r2_dir, "R2_inv_p3", 20000, 80000, pattern_3_a, pattern_3_b)
    save_input_pair(r2_dir, "R2_inv_p4", 20000, 80000, pattern_4_a, pattern_4_b)
    save_input_pair(r2_dir, "R2_inv_random", 20000, 80000, random_pattern_a, random_pattern_b)

    # R3 8:1 big (direto e invertido)
    r3_dir = os.path.join(big_dir, "R3")
    save_input_pair(r3_dir, "R3_p1", 80000, 10000, pattern_1_a, pattern_1_b)
    save_input_pair(r3_dir, "R3_p2", 80000, 10000, pattern_2_a, pattern_2_b)
    save_input_pair(r3_dir, "R3_p3", 80000, 10000, pattern_3_a, pattern_3_b)
    save_input_pair(r3_dir, "R3_p4", 80000, 10000, pattern_4_a, pattern_4_b)
    save_input_pair(r3_dir, "R3_random", 80000, 10000, random_pattern_a, random_pattern_b)

    save_input_pair(r3_dir, "R3_inv_p1", 10000, 80000, pattern_1_a, pattern_1_b)
    save_input_pair(r3_dir, "R3_inv_p2", 10000, 80000, pattern_2_a, pattern_2_b)
    save_input_pair(r3_dir, "R3_inv_p3", 10000, 80000, pattern_3_a, pattern_3_b)
    save_input_pair(r3_dir, "R3_inv_p4", 10000, 80000, pattern_4_a, pattern_4_b)
    save_input_pair(r3_dir, "R3_inv_random", 10000, 80000, random_pattern_a, random_pattern_b)

    # gigas (não tão usando todos os padrões pra não demorar tanto)

    # R4 2:1 giga (direto e invertido)
    r4_dir = os.path.join(giga_dir, "R4")
    save_input_pair(r4_dir, "R4_p1", 160000, 80000, pattern_1_a, pattern_1_b)
    save_input_pair(r4_dir, "R4_inv_p1", 80000, 160000, pattern_1_a, pattern_1_b)

    # R5 4:1 giga (direto e invertido)
    r5_dir = os.path.join(giga_dir, "R5")
    save_input_pair(r5_dir, "R5_p1", 160000, 40000, pattern_1_a, pattern_1_b)
    save_input_pair(r5_dir, "R5_inv_p1", 40000, 160000, pattern_1_a, pattern_1_b)

    # R6 8:1 giga (direto e invertido)
    r6_dir = os.path.join(giga_dir, "R6")
    save_input_pair(r6_dir, "R6_p1", 160000, 20000, pattern_1_a, pattern_1_b)
    save_input_pair(r6_dir, "R6_inv_p1", 20000, 160000, pattern_1_a, pattern_1_b)

    # quadrados gigantes --mem_opt
    # Q7 usando todos os padrões
    q7_dir = os.path.join(giga_dir, "Q7")
    save_input_pair(q7_dir, "Q7_p1", 160000, 160000, pattern_1_a, pattern_1_b)
    save_input_pair(q7_dir, "Q7_p2", 160000, 160000, pattern_2_a, pattern_2_b)
    save_input_pair(q7_dir, "Q7_p3", 160000, 160000, pattern_3_a, pattern_3_b)
    save_input_pair(q7_dir, "Q7_p4", 160000, 160000, pattern_4_a, pattern_4_b)
    save_input_pair(q7_dir, "Q7_random", 160000, 160000, random_pattern_a, random_pattern_b)

    q8_dir = os.path.join(giga_dir, "Q8")
    save_input_pair(q8_dir, "Q8_p1", 320000, 320000, pattern_1_a, pattern_1_b)
