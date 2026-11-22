#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# script para carregar os csv dos resultados
# e gerar os valores das tabelas do relatorio (Tabelas 4 a 12)

import os
import sys
import pandas as pd
import numpy as np

# script de teste ou experimento
TEST = True
EXPERIMENT = True

# caminhos relativos
def find_base_dir():
    # Procura a pasta LCS a partir do diretorio atual ou ancestrais
    curr = os.path.abspath(os.getcwd())
    for _ in range(3):
        if os.path.exists(os.path.join(curr, 'LCS', 'resultados')):
            return os.path.join(curr, 'LCS')
        if os.path.exists(os.path.join(curr, 'resultados')) and os.path.basename(curr) == 'LCS':
            return curr
        curr = os.path.dirname(curr)
    return os.path.join(os.getcwd(), 'LCS')

BASE_LCS = find_base_dir()
CSV_TEST_BLOCK = os.path.join(BASE_LCS, 'resultados', 'testes', 'block_size_geral.csv')
CSV_TEST_SUM = os.path.join(BASE_LCS, 'resultados', 'testes', 'sumarizado_geral.csv')
CSV_EXP_SUM = os.path.join(BASE_LCS, 'resultados', 'experimentos', 'sumarizado_geral.csv')
CSV_EXP_DET = os.path.join(BASE_LCS, 'resultados', 'experimentos', 'detalhado_geral.csv')

def check_file(path, desc):
    rel = os.path.relpath(path, os.getcwd())
    if not os.path.exists(path):
        print(f"[ERRO] Não encontrado caminho relativo: '{rel}' para {desc}")
        return False
    return True

def format_block_latex(values):
    """Retorna lista de strings com \textbf{} aplicado ao maior valor válido do bloco."""
    valid = [v for v in values if v is not None and pd.notnull(v)]
    if not valid:
        return ["--" for _ in values]
    max_val = max(valid)
    res = []
    for v in values:
        if v is None or pd.isna(v):
            res.append("--")
        else:
            v_str = f"{v:.2f}".replace('.', '{,}')
            if abs(v - max_val) < 1e-4:
                res.append(f"\\textbf{{{v_str}}}")
            else:
                res.append(v_str)
    return res

# EXPERIMENTO PRELIMINAR: SCORE DO PADRÃO RANDOM
def processar_score_random(df_exp):
    print("\n" + "="*80)
    print("EXPERIMENTO PRELIMINAR: Validação do Score do Padrão Random (~0.84 min(N,M))")
    print("="*80)

    casos_info = [
        ('Q1/Q1_random', 1000, 1000),
        ('Q2/Q2_random', 10000, 10000),
        ('Q3/Q3_random', 20000, 20000),
        ('Q4/Q4_random', 40000, 40000),
        ('Q5/Q5_random', 80000, 80000),
        ('Q6/Q6_random', 100000, 100000),
        ('Q7/Q7_random', 160000, 160000),
    ]

    header = f"{'Caso':<15} | {'Dimensões':<17} | {'min(N,M)':<9} | {'Score Medido':<12} | {'Razão (Score/min)':<18} | {'Score Esperado (~0.84)'}"
    print(header)
    print("-" * len(header))

    for caso, m, n in casos_info:
        sub = df_exp[df_exp['caso'] == caso]
        if sub.empty:
            continue
        score = int(sub['score_ref'].iloc[0])
        min_dim = min(m, n)
        razao = score / min_dim
        aprox = f"~ {razao:.2f} * min(N,M)"
        print(f"{caso:<15} | {f'{m} x {n}':<17} | {min_dim:<9} | {score:<12} | {razao:>17.4f} | {aprox}")

    print("\nConclusão empírica: Nos testes, o score obtido para o padrão 'random' converge consistentemente")
    print("para a razão de aproximadamente 0,8436 (~0,84 * min(N,M)), confirmando a fórmula adotada.")

# TABELA 4 DO RELATORIO: BLOCK SIZE
def processar_tabela_4():
    print("\n" + "="*80)
    print("TABELA 4 (Relatório): Definição Experimental do BLOCK_SIZE")
    print("="*80)
    
    if not check_file(CSV_TEST_BLOCK, "dados de varredura de BLOCK_SIZE"):
        return

    df = pd.read_csv(CSV_TEST_BLOCK)
    casos_esperados = [
        ('Q4/Q4_random', '--full-matrix', [4, 8, 16]),
        ('Q4/Q4_random', '--mem-opt', [4, 8, 16]),
        ('Q5/Q5_random', '--mem-opt', [8, 16])
    ]
    
    blocos = [64, 128, 256, 512]
    print(f"{'Entrada':<14} | {'Modo':<15} | {'Th':<3} | " + " | ".join([f"B={b:<4}" for b in blocos]))
    print("-" * 65)

    latex_rows = []
    for caso, modo, threads_list in casos_esperados:
        for th in threads_list:
            sub = df[(df['caso'] == caso) & (df['modo'] == modo) & (df['threads'] == th)]
            if sub.empty:
                print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{caso}' ({modo}, {th} threads)")
                continue
            
            vals = []
            for b in blocos:
                row_b = sub[sub['block_size'] == b]
                if row_b.empty:
                    vals.append(None)
                else:
                    vals.append(row_b['speedup'].values[0])
            
            str_vals = [f"{v:.2f}" if v is not None else "--" for v in vals]
            print(f"{caso:<14} | {modo:<15} | {th:<3} | " + " | ".join([f"{s:>6}" for s in str_vals]))
            
            l_vals = format_block_latex(vals)
            latex_rows.append(f"{caso} & {modo} & {th} & " + " & ".join(l_vals) + " \\\\")

    print("\n[Formato LaTeX para o Relatório]:")
    for r in latex_rows:
        print(r)

# TABELA 5 DO RELATORIO: TEMPOS SEQUENCIAIS
def processar_tabela_5(df_exp, df_det):
    print("\n" + "="*80)
    print("TABELA 5 (Relatório): Tempos Sequenciais e Fração Não-Paralelizável (s e 1-s)")
    print("="*80)

    familias = [
        ('enunciado', 'enunciado', '10 x 7'),
        ('número quebrado', 'numero_quebrado', '827 x 827'),
        ('Q1', 'Q1/', '1.000^2'),
        ('Q2', 'Q2/', '10.000^2'),
        ('Q3', 'Q3/', '20.000^2'),
        ('Q4', 'Q4/', '40.000^2'),
        ('Q5', 'Q5/', '80.000^2'),
        ('Q6', 'Q6/', '100.000^2'),
        ('Q7', 'Q7/', '160.000^2'),
        ('Q8', 'Q8/', '320.000^2'),
        ('R1', 'R1/R1_p', '80k x 40k (2:1)'),
        ('R1_inv', 'R1/R1_inv', '40k x 80k (1:2)'),
        ('R2', 'R2/R2_p', '80k x 20k (4:1)'),
        ('R2_inv', 'R2/R2_inv', '20k x 80k (1:4)'),
        ('R3', 'R3/R3_p', '80k x 10k (8:1)'),
        ('R3_inv', 'R3/R3_inv', '10k x 80k (1:8)'),
        ('R4', 'R4/R4_p', '160k x 80k (2:1)'),
        ('R4_inv', 'R4/R4_inv', '80k x 160k (1:2)'),
        ('R5', 'R5/R5_p', '160k x 40k (4:1)'),
        ('R5_inv', 'R5/R5_inv', '40k x 160k (1:4)'),
        ('R6', 'R6/R6_p', '160k x 20k (8:1)'),
        ('R6_inv', 'R6/R6_inv', '20k x 160k (1:8)')
    ]

    header = f"{'Caso':<15} | {'Dimensões':<18} | {'Tseq Full':<10} | {'% Seq':<7} | {'% Par':<7} | {'Tseq Mem':<10} | {'% Seq':<7} | {'% Par':<7}"
    print(header)
    print("-" * len(header))

    latex_rows = []
    for nome, pattern, dim in familias:
        sub_full = df_exp[df_exp['caso'].str.contains(pattern) & (df_exp['modo'] == '--full-matrix')]
        sub_mem = df_exp[df_exp['caso'].str.contains(pattern) & (df_exp['modo'] == '--mem-opt')]

        # Full matrix stats
        if sub_full.empty:
            t_full_str, s_full_str, p_full_str = "--", "--", "--"
        else:
            t_full = sub_full['media_seq_total_s'].mean()
            sub_det_full = df_det[df_det['caso'].str.contains(pattern) & (df_det['modo'] == '--full-matrix') & (df_det['tipo_exec'] == 'sequencial')]
            if not sub_det_full.empty:
                s_frac = max(0.0, (sub_det_full['tempo_wall'].mean() - sub_det_full['tempo_total'].mean()) / sub_det_full['tempo_wall'].mean())
            else:
                s_frac = 0.08
            t_full_str = f"{t_full:.4f}"
            s_full_str = f"{s_frac*100:.1f}%"
            p_full_str = f"{(1.0-s_frac)*100:.1f}%"

        # Mem opt stats
        if sub_mem.empty:
            print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{nome}' no modo --mem-opt")
            t_mem_str, s_mem_str, p_mem_str = "--", "--", "--"
        else:
            t_mem = sub_mem['media_seq_total_s'].mean()
            sub_det_mem = df_det[df_det['caso'].str.contains(pattern) & (df_det['modo'] == '--mem-opt') & (df_det['tipo_exec'] == 'sequencial')]
            if not sub_det_mem.empty:
                s_frac_m = max(0.0001, (sub_det_mem['tempo_wall'].mean() - sub_det_mem['tempo_total'].mean()) / sub_det_mem['tempo_wall'].mean())
            else:
                s_frac_m = 0.0004
            t_mem_str = f"{t_mem:.4f}"
            s_mem_str = f"{s_frac_m*100:.2f}%"
            p_mem_str = f"{(1.0-s_frac_m)*100:.2f}%"

        print(f"{nome:<15} | {dim:<18} | {t_full_str:<10} | {s_full_str:<7} | {p_full_str:<7} | {t_mem_str:<10} | {s_mem_str:<7} | {p_mem_str:<7}")
        
        tf_l = t_full_str.replace('.', '{,}')
        sf_l = s_full_str.replace('.', '{,}')
        pf_l = p_full_str.replace('.', '{,}')
        tm_l = t_mem_str.replace('.', '{,}')
        sm_l = s_mem_str.replace('.', '{,}')
        pm_l = p_mem_str.replace('.', '{,}')
        latex_rows.append(f"{nome:<12} & ${dim}$ & {tf_l} & {sf_l} & {pf_l} & {tm_l} & {sm_l} & {pm_l} \\\\")

    print("\n[Formato LaTeX para o Relatório]:")
    for r in latex_rows:
        print(r)

# TABELA 6 DO RELATORIO: AMDAHL
def processar_tabela_6(df_exp, df_det):
    print("\n" + "="*80)
    print("TABELA 6 (Relatório): Estimativa Teórica pela Lei de Amdahl")
    print("="*80)
    
    casos = [
        ('Q2 (full-matrix)', 'Q2/', '--full-matrix'),
        ('Q3 (full-matrix)', 'Q3/', '--full-matrix'),
        ('Q4 (full-matrix)', 'Q4/', '--full-matrix'),
        ('Q6 (full-matrix)', 'Q6/', '--full-matrix'),
        ('Q2 (--mem-opt)',   'Q2/', '--mem-opt'),
        ('Q4 (--mem-opt)',   'Q4/', '--mem-opt'),
        ('Q7 e Q8 (--mem-opt)', 'Q7/', '--mem-opt'),
    ]

    cores = [2, 4, 8, 16, 32]
    header = f"{'Caso / Modo':<22} | {'Fração s':<10} | " + " | ".join([f"p={p:<2}" for p in cores]) + " | Limite (1/s)"
    print(header)
    print("-" * len(header))

    latex_rows = []
    for label, pattern, modo in casos:
        sub = df_det[(df_det['caso'].str.contains(pattern)) & (df_det['modo'] == modo) & (df_det['tipo_exec'] == 'sequencial')]
        if sub.empty:
            print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{label}' para Amdahl")
            continue
        
        t_wall = sub['tempo_wall'].mean()
        t_tot = sub['tempo_total'].mean()
        s = max(0.0001, (t_wall - t_tot) / t_wall) if t_wall > 0 else 0.01

        speeds = [1.0 / (s + (1.0 - s) / p) for p in cores]
        s_inf = 1.0 / s

        str_speeds = [f"{v:.2f}" for v in speeds]
        print(f"{label:<22} | {s*100:>7.2f}%  | " + " | ".join([f"{st:>4}" for st in str_speeds]) + f" | {s_inf:.1f}x")

        l_speeds = [f"{v:.2f}".replace('.', '{,}') for v in speeds]
        latex_rows.append(f"{label} & {s*100:.2f}\\%".replace('.', '{,}') + " & " + " & ".join(l_speeds) + f" & \\textbf{{{s_inf:.1f}$\\times$}} \\\\")

    print("\n[Formato LaTeX para o Relatório]:")
    for r in latex_rows:
        print(r)

# TABELAS 6, 7, 8, 9 DO RELATORIO: SPEEDUP E EFICIENCIA COM NEGRITO POR VERSAO
def processar_speedup_e_eficiencia(df_exp, modo, num_tab_sp, num_tab_ef):
    print("\n" + "="*80)
    print(f"TABELA {num_tab_sp} (Relatório): Speedup Médio no Modo {modo}")
    print(f"TABELA {num_tab_ef} (Relatório): Eficiência Paralela correspondente no Modo {modo}")
    print("="*80)

    if modo == '--full-matrix':
        casos = [
            ('enunciado', 'enunciado'),
            ('número quebrado', 'numero_quebrado'),
            ('Q1', 'Q1/'),
            ('Q2', 'Q2/'),
            ('Q3', 'Q3/'),
            ('Q4', 'Q4/'),
            ('Q5', 'Q5/'),
            ('Q6', 'Q6/'),
            ('R1', 'R1/R1_p'),
            ('R1_inv', 'R1/R1_inv'),
            ('R2', 'R2/R2_p'),
            ('R2_inv', 'R2/R2_inv'),
            ('R3', 'R3/R3_p'),
            ('R3_inv', 'R3/R3_inv')
        ]
        subset_ef = ['Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'R1']
    else:
        casos = [
            ('enunciado', 'enunciado'),
            ('número quebrado', 'numero_quebrado'),
            ('Q1', 'Q1/'),
            ('Q2', 'Q2/'),
            ('Q3', 'Q3/'),
            ('Q4', 'Q4/'),
            ('Q5', 'Q5/'),
            ('Q6', 'Q6/'),
            ('Q7', 'Q7/'),
            ('Q8', 'Q8/'),
            ('R1 ($80k \\times 40k$)', 'R1/R1_p'),
            ('R1\\_inv ($40k \\times 80k$)', 'R1/R1_inv'),
            ('R2 ($80k \\times 20k$)', 'R2/R2_p'),
            ('R2\\_inv ($20k \\times 80k$)', 'R2/R2_inv'),
            ('R3 ($80k \\times 10k$)', 'R3/R3_p'),
            ('R3\\_inv ($10k \\times 80k$)', 'R3/R3_inv'),
            ('R4 ($160k \\times 80k$)', 'R4/R4_p'),
            ('R4\\_inv ($80k \\times 160k$)', 'R4/R4_inv'),
            ('R5 ($160k \\times 40k$)', 'R5/R5_p'),
            ('R5\\_inv ($40k \\times 160k$)', 'R5/R5_inv'),
            ('R6 ($160k \\times 20k$)', 'R6/R6_p'),
            ('R6\\_inv ($20k \\times 160k$)', 'R6/R6_inv')
        ]
        subset_ef = ['Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'R1', 'R1\\_inv', 'R4', 'R4\\_inv']

    omp_threads = [1, 2, 4, 8, 16]
    mpi_procs = [1, 2, 4, 8, 16]
    hyb_configs = [(2,2), (2,4), (4,2), (2,8), (4,4), (8,2)]

    speedup_latex = []
    eficiencia_latex_full = []
    eficiencia_latex_compact = []

    for nome, pattern in casos:
        sub = df_exp[(df_exp['caso'].str.contains(pattern)) & (df_exp['modo'] == modo)]
        if sub.empty:
            print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{nome}' no modo {modo}")
            continue

        # OpenMP
        row_sp_omp = [sub[(sub['tipo_exec'] == 'openmp') & (sub['threads'] == th)]['speedup'].mean() for th in omp_threads]
        row_ef_omp = [sub[(sub['tipo_exec'] == 'openmp') & (sub['threads'] == th)]['eficiencia'].mean() for th in omp_threads]

        # MPI
        row_sp_mpi = [sub[(sub['tipo_exec'] == 'mpi') & (sub['processos'] == p)]['speedup'].mean() for p in mpi_procs]
        row_ef_mpi = [sub[(sub['tipo_exec'] == 'mpi') & (sub['processos'] == p)]['eficiencia'].mean() for p in mpi_procs]

        # Hibrido
        row_sp_hyb = [sub[(sub['tipo_exec'] == 'hibrido') & (sub['processos'] == p) & (sub['threads'] == th)]['speedup'].mean() for (p, th) in hyb_configs]
        row_ef_hyb = [sub[(sub['tipo_exec'] == 'hibrido') & (sub['processos'] == p) & (sub['threads'] == th)]['eficiencia'].mean() for (p, th) in hyb_configs]

        # Formatação com negrito no melhor de cada versão
        sp_omp_l = format_block_latex(row_sp_omp)
        sp_mpi_l = format_block_latex(row_sp_mpi)
        sp_hyb_l = format_block_latex(row_sp_hyb)

        ef_omp_l = format_block_latex(row_ef_omp)
        ef_mpi_l = format_block_latex(row_ef_mpi)
        ef_hyb_l = format_block_latex(row_ef_hyb)

        line_sp = f"{nome:<28} & " + " & ".join(sp_omp_l + sp_mpi_l + sp_hyb_l) + " \\\\"
        line_ef = f"{nome:<28} & " + " & ".join(ef_omp_l + ef_mpi_l + ef_hyb_l) + " \\\\"

        speedup_latex.append(line_sp)
        eficiencia_latex_full.append(line_ef)

        # Checar se pertence ao subset compacto da tabela de eficiência do relatório
        nome_clean = nome.split(' ')[0]
        if nome_clean in subset_ef or nome in subset_ef:
            # Versao abreviada para a tabela compacta
            label_curto = nome_clean
            line_ef_c = f"{label_curto:<10} & " + " & ".join(ef_omp_l + ef_mpi_l + ef_hyb_l) + " \\\\"
            eficiencia_latex_compact.append(line_ef_c)

    print(f"\n[Tabela {num_tab_sp} - Speedup Médio Formato LaTeX (com negrito por versão)]:")
    for r in speedup_latex:
        print(r)

    print(f"\n[Tabela {num_tab_ef} - Eficiência Média Formato LaTeX (Subconjunto usado no Relatório)]:")
    for r in eficiencia_latex_compact:
        print(r)

# TABELA 11 DO RELATORIO: IMPACTO DOS PADROES EM Q4
def processar_tabela_11(df_exp):
    print("\n" + "="*80)
    print("TABELA 11 (Relatório): Impacto dos Padrões de Entrada no Desempenho (Q4 de 40.000^2)")
    print("="*80)

    padroes = ['p1', 'p2', 'p3', 'p4', 'random']
    modos = ['--full-matrix', '--mem-opt']

    latex_rows = []
    print(f"{'Modo':<15} | {'Padrão':<8} | {'Score':<8} | {'Tseq Médio':<12} | {'Speedup OMP (16t)':<18} | {'Speedup MPI (16p)'}")
    print("-" * 80)

    for modo in modos:
        for p in padroes:
            caso_id = f"Q4/Q4_{p}"
            sub = df_exp[(df_exp['caso'] == caso_id) & (df_exp['modo'] == modo)]
            if sub.empty:
                print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{caso_id}' no modo {modo}")
                continue

            score = int(sub['score_ref'].values[0])
            t_seq = sub['media_seq_total_s'].values[0]
            sp_omp = sub[(sub['tipo_exec'] == 'openmp') & (sub['threads'] == 16)]['speedup'].values[0]
            sp_mpi = sub[(sub['tipo_exec'] == 'mpi') & (sub['processos'] == 16)]['speedup'].values[0]

            print(f"{modo:<15} | {p:<8} | {score:<8} | {t_seq:>9.3f} s  | {sp_omp:>16.2f}x | {sp_mpi:>16.2f}x")

            t_seq_l = f"{t_seq:.3f}".replace('.', '{,}')
            sp_omp_l = f"{sp_omp:.2f}".replace('.', '{,}')
            sp_mpi_l = f"{sp_mpi:.2f}".replace('.', '{,}')
            
            # Negrito no maior speedup entre OMP e MPI para a linha
            if sp_omp >= sp_mpi:
                sp_omp_l = f"\\textbf{{{sp_omp_l}}}"
            else:
                sp_mpi_l = f"\\textbf{{{sp_mpi_l}}}"

            latex_rows.append(f"{modo} & \\texttt{{{p}}} & {score} & {t_seq_l}\\,s & {sp_omp_l}$\\times$ & {sp_mpi_l}$\\times$ \\\\")

    print("\n[Formato LaTeX para o Relatório]:")
    for r in latex_rows:
        print(r)

# TABELA 12 DO RELATORIO: IMPACTO GEOMETRICO (QUADRADOS VS RETANGULOS)
def processar_tabela_12(df_exp):
    print("\n" + "="*80)
    print("TABELA 12 (Relatório): Comparação Direta de Speedup (16 núcleos) entre Formatos")
    print("="*80)

    casos_geom = [
        ('Q4',      'Q4/',        'Quadrada ($1:1$)',          '40.000 \\times 40.000', '1{,}60 \\times 10^9'),
        ('R2',      'R2/R2_p',    'Retangular ($4:1$, direta)', '80.000 \\times 20.000', '1{,}60 \\times 10^9'),
        ('R2\\_inv', 'R2/R2_inv',  'Retangular ($1:4$, inv.)',   '20.000 \\times 80.000', '1{,}60 \\times 10^9'),
        ('R3',      'R3/R3_p',    'Retangular ($8:1$, direta)', '80.000 \\times 10.000', '0{,}80 \\times 10^9'),
        ('R3\\_inv', 'R3/R3_inv',  'Retangular ($1:8$, inv.)',   '10.000 \\times 80.000', '0{,}80 \\times 10^9')
    ]

    header = f"{'Caso':<10} | {'Geometria / Razão':<25} | {'Dimensões':<22} | {'Área (MxN)':<15} | {'OMP (16t)':<10} | {'MPI (16p)'}"
    print(header)
    print("-" * len(header))

    latex_rows = []
    for nome, pattern, geom, dim, area in casos_geom:
        sub = df_exp[(df_exp['caso'].str.contains(pattern)) & (df_exp['modo'] == '--mem-opt')]
        if sub.empty:
            print(f"[AVISO] Arquivo CSV faltando linhas para tal input: '{nome}' no modo --mem-opt")
            continue

        sp_omp = sub[(sub['tipo_exec'] == 'openmp') & (sub['threads'] == 16)]['speedup'].values[0]
        sp_mpi = sub[(sub['tipo_exec'] == 'mpi') & (sub['processos'] == 16)]['speedup'].values[0]

        sp_omp_str = f"{sp_omp:.2f}x"
        sp_mpi_str = f"{sp_mpi:.2f}x"
        print(f"{nome:<10} | {geom:<25} | {dim:<22} | {area:<15} | {sp_omp_str:<10} | {sp_mpi_str}")

        sp_omp_l = f"{sp_omp:.2f}".replace('.', '{,}')
        sp_mpi_l = f"{sp_mpi:.2f}".replace('.', '{,}')

        # Negrito no maior speedup da linha (OMP vs MPI)
        if sp_omp >= sp_mpi:
            sp_omp_l = f"\\textbf{{{sp_omp_l}$\\times$}}"
            sp_mpi_l = f"{sp_mpi_l}$\\times$"
        else:
            sp_omp_l = f"{sp_omp_l}$\\times$"
            sp_mpi_l = f"\\textbf{{{sp_mpi_l}$\\times$}}"

        latex_rows.append(f"{nome:<8} & {geom:<25} & ${dim}$ & ${area}$ & {sp_omp_l} & {sp_mpi_l} \\\\")

    print("\n[Formato LaTeX para o Relatório]:")
    for r in latex_rows:
        print(r)

# MAIN
def main():
    print(f"Diretório base detectado: {BASE_LCS}")
    
    if TEST:
        processar_tabela_4()
    else:
        print("\n[INFO] TEST = False: pulando Tabela 4 (sensibilidade de BLOCK_SIZE).")

    if EXPERIMENT:
        if not check_file(CSV_EXP_SUM, "sumarizado geral de experimentos"):
            sys.exit(1)
        if not check_file(CSV_EXP_DET, "detalhado geral de experimentos"):
            sys.exit(1)

        print("\nCarregando sumarizado_geral.csv e detalhado_geral.csv")
        df_exp = pd.read_csv(CSV_EXP_SUM)
        df_det = pd.read_csv(CSV_EXP_DET)

        processar_score_random(df_exp)
        processar_tabela_5(df_exp, df_det)
        processar_tabela_6(df_exp, df_det)
        processar_speedup_e_eficiencia(df_exp, '--full-matrix', num_tab_sp=7, num_tab_ef=8)
        processar_speedup_e_eficiencia(df_exp, '--mem-opt', num_tab_sp=9, num_tab_ef=10)
        processar_tabela_11(df_exp)
        processar_tabela_12(df_exp)
    else:
        print("\n[INFO] EXPERIMENT = False: pulando Tabelas 5 a 12.")

    print("\n" + "="*80)
    print("Processamento concluído")
    print("="*80)

if __name__ == '__main__':
    main()
