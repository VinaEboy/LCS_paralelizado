import os
import sys
import csv
import json
import shutil
from datetime import datetime

# diretorios principais
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from utils_experiment import (
    collect_system_metadata,
    ensure_binaries,
    ensure_inputs,
    run_single_execution
)

# diretorios principais
script_dir = os.path.dirname(os.path.abspath(__file__))
lcs_dir = os.path.abspath(os.path.join(script_dir, ".."))
inputs_dir = os.path.join(lcs_dir, "inputs")
results_dir = os.path.join(lcs_dir, "resultados")

# caminhos dos executaveis
seq_bin = os.path.join(lcs_dir, "lcs_seq")
omp_bin = os.path.join(lcs_dir, "lcs_omp")
mpi_bin = os.path.join(lcs_dir, "lcs_mpi")
hybrid_bin = os.path.join(lcs_dir, "lcs_hybrid")

# configuracoes fixas dos experimentos (sem argumentos de linha de comando)
threads_list = [1, 2, 4, 8, 16]
mpi_processes_list = [1, 2, 4, 8, 16]
hybrid_configs = [(2, 2), (2, 4), (4, 2), (2, 8), (4, 4), (8, 2)]
repetitions = 20

# lista completa de casos de teste estruturada por subpastas de categorias
test_cases = [
    # enunciado e numero quebrado na raiz de small
    ("small", "enunciado",              ["--full-matrix", "--mem-opt"]),
    ("small", "numero_quebrado",        ["--full-matrix", "--mem-opt"]),

    # quadrados small (Q1 a Q4)
    ("small", "Q1/Q1_p1",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q1/Q1_p2",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q1/Q1_p3",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q1/Q1_p4",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q1/Q1_random",           ["--full-matrix", "--mem-opt"]),

    ("small", "Q2/Q2_p1",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q2/Q2_p2",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q2/Q2_p3",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q2/Q2_p4",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q2/Q2_random",           ["--full-matrix", "--mem-opt"]),

    ("small", "Q3/Q3_p1",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q3/Q3_p2",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q3/Q3_p3",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q3/Q3_p4",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q3/Q3_random",           ["--full-matrix", "--mem-opt"]),

    ("small", "Q4/Q4_p1",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q4/Q4_p2",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q4/Q4_p3",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q4/Q4_p4",               ["--full-matrix", "--mem-opt"]),
    ("small", "Q4/Q4_random",           ["--full-matrix", "--mem-opt"]),

    # quadrados big (Q5 e Q6)
    ("big",   "Q5/Q5_p1",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q5/Q5_p2",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q5/Q5_p3",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q5/Q5_p4",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q5/Q5_random",           ["--full-matrix", "--mem-opt"]),

    ("big",   "Q6/Q6_p1",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q6/Q6_p2",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q6/Q6_p3",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q6/Q6_p4",               ["--full-matrix", "--mem-opt"]),
    ("big",   "Q6/Q6_random",           ["--full-matrix", "--mem-opt"]),

    # retangulos big (diretos e invertidos)
    ("big",   "R1/R1_p1",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_p2",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_p3",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_p4",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_random",           ["--full-matrix", "--mem-opt"]),

    ("big",   "R1/R1_inv_p1",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_inv_p2",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_inv_p3",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_inv_p4",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R1/R1_inv_random",       ["--full-matrix", "--mem-opt"]),

    ("big",   "R2/R2_p1",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_p2",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_p3",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_p4",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_random",           ["--full-matrix", "--mem-opt"]),

    ("big",   "R2/R2_inv_p1",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_inv_p2",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_inv_p3",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_inv_p4",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R2/R2_inv_random",       ["--full-matrix", "--mem-opt"]),

    ("big",   "R3/R3_p1",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_p2",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_p3",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_p4",               ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_random",           ["--full-matrix", "--mem-opt"]),

    ("big",   "R3/R3_inv_p1",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_inv_p2",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_inv_p3",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_inv_p4",           ["--full-matrix", "--mem-opt"]),
    ("big",   "R3/R3_inv_random",       ["--full-matrix", "--mem-opt"]),

    # gigas retangulos (diretos e invertidos)
    ("giga",  "R4/R4_p1",               ["--mem-opt"]),
    ("giga",  "R4/R4_inv_p1",           ["--mem-opt"]),
    ("giga",  "R5/R5_p1",               ["--mem-opt"]),
    ("giga",  "R5/R5_inv_p1",           ["--mem-opt"]),
    ("giga",  "R6/R6_p1",               ["--mem-opt"]),
    ("giga",  "R6/R6_inv_p1",           ["--mem-opt"]),

    # gigas quadrados (Q7 com todos os padroes e Q8)
    ("giga",  "Q7/Q7_p1",               ["--mem-opt"]),
    ("giga",  "Q7/Q7_p2",               ["--mem-opt"]),
    ("giga",  "Q7/Q7_p3",               ["--mem-opt"]),
    ("giga",  "Q7/Q7_p4",               ["--mem-opt"]),
    ("giga",  "Q7/Q7_random",           ["--mem-opt"]),
    ("giga",  "Q8/Q8_p1",               ["--mem-opt"]),
]

def main():
    # flush imediato para logs com nohup
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    ensure_binaries(lcs_dir)
    ensure_inputs(script_dir)

    os.makedirs(results_dir, exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # grava o arquivo de configuracao do ambiente 
    env_info = collect_system_metadata()
    env_info_path = os.path.join(results_dir, f"ambiente_info_{now_str}.json")
    with open(env_info_path, "w") as f:
        json.dump(env_info, f, indent=2)
    print(f"metadados do ambiente salvos em: {env_info_path}")

    # prepara variaveis de ambiente
    run_env = os.environ.copy()
    run_env["OMP_PROC_BIND"] = "close"
    run_env["OMP_PLACES"] = "cores"

    csv_detail_path = os.path.join(results_dir, f"experimento_detalhado_{now_str}.csv")
    csv_summary_path = os.path.join(results_dir, f"experimento_sumarizado_{now_str}.csv")

    detail_fieldnames = [
        "timestamp", "tipo_exec", "caso", "modo", "processos", "threads", "repeticao",
        "score", "correto", "tempo_seq", "tempo_par", "tempo_total", "tempo_wall",
        "temp_start", "temp_end", "freq_start_mhz", "freq_end_mhz", "load_start", "mem_start_mb",
        "returncode"
    ]

    detail_file = open(csv_detail_path, "w", newline="")
    detail_writer = csv.DictWriter(detail_file, fieldnames=detail_fieldnames)
    detail_writer.writeheader()
    detail_file.flush()

    summary_records = []

    print(f"arquivos de resultados:")
    print(f"  detalhado:  {csv_detail_path}")
    print(f"  sumarizado: {csv_summary_path}\n")

    for cat, case_rel_path, allowed_modes in test_cases:
        case_full_path = os.path.join(inputs_dir, cat, case_rel_path)
        file_a = os.path.join(case_full_path, "fileA.in")
        file_b = os.path.join(case_full_path, "fileB.in")

        if not os.path.exists(file_a) or not os.path.exists(file_b):
            print(f"aviso: arquivos para o caso {case_rel_path} nao encontrados em {case_full_path}, pulando")
            continue

        print(f"--------------------------------------------------")
        print(f"caso: {case_rel_path}")
        print(f"--------------------------------------------------")

        for mode in allowed_modes:
            # 1. execucao sequencial (20 repeticoes)
            print(f"executando sequencial para {case_rel_path} [{mode}] ({repetitions}x)...")
            seq_scores = []
            seq_totals = []

            for rep in range(1, repetitions + 1):
                cmd = [seq_bin, file_a, file_b, mode]
                score, t_seq, _, t_total, telem = run_single_execution(cmd, run_env)

                seq_scores.append(score)
                if t_total is not None:
                    seq_totals.append(t_total)
                else:
                    seq_totals.append(telem["wall_time"])

                detail_writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "tipo_exec": "sequencial",
                    "caso": case_rel_path,
                    "modo": mode,
                    "processos": 1,
                    "threads": 1,
                    "repeticao": rep,
                    "score": score,
                    "correto": 1,
                    "tempo_seq": t_seq,
                    "tempo_par": 0.0,
                    "tempo_total": t_total,
                    "tempo_wall": telem["wall_time"],
                    "temp_start": telem["temp_start"],
                    "temp_end": telem["temp_end"],
                    "freq_start_mhz": telem["freq_start"],
                    "freq_end_mhz": telem["freq_end"],
                    "load_start": telem["load_start"],
                    "mem_start_mb": telem["mem_start_mb"],
                    "returncode": telem["returncode"]
                })
                detail_file.flush()

            ref_score = seq_scores[0] if seq_scores else None
            avg_seq_time = sum(seq_totals) / len(seq_totals) if seq_totals else 0.0
            print(f"  sequencial concluido: media={avg_seq_time:.4f}s, score_ref={ref_score}")

            # execucoes paralelas openmp (20 repeticoes por numero de threads)
            for num_threads in threads_list:
                print(f"  executando openmp {num_threads} threads [{mode}] ({repetitions}x)...")
                par_scores = []
                par_times = []
                total_times = []
                divergencias = 0

                for rep in range(1, repetitions + 1):
                    cmd = [omp_bin, file_a, file_b, str(num_threads), mode]
                    score, t_seq, t_par, t_total, telem = run_single_execution(cmd, run_env)

                    is_correct = 1 if (ref_score is not None and score == ref_score) else 0
                    if not is_correct:
                        divergencias += 1

                    par_scores.append(score)
                    if t_par is not None:
                        par_times.append(t_par)
                    if t_total is not None:
                        total_times.append(t_total)
                    else:
                        total_times.append(telem["wall_time"])

                    detail_writer.writerow({
                        "timestamp": datetime.now().isoformat(),
                        "tipo_exec": "openmp",
                        "caso": case_rel_path,
                        "modo": mode,
                        "processos": 1,
                        "threads": num_threads,
                        "repeticao": rep,
                        "score": score,
                        "correto": is_correct,
                        "tempo_seq": t_seq,
                        "tempo_par": t_par,
                        "tempo_total": t_total,
                        "tempo_wall": telem["wall_time"],
                        "temp_start": telem["temp_start"],
                        "temp_end": telem["temp_end"],
                        "freq_start_mhz": telem["freq_start"],
                        "freq_end_mhz": telem["freq_end"],
                        "load_start": telem["load_start"],
                        "mem_start_mb": telem["mem_start_mb"],
                        "returncode": telem["returncode"]
                    })
                    detail_file.flush()

                avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                
                std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                eficiencia = (speedup / num_threads) if num_threads > 0 else 0.0

                if divergencias > 0:
                    print(f"    aviso: {divergencias} divergencias de score detectadas")

                summary_records.append({
                    "caso": case_rel_path,
                    "modo": mode,
                    "tipo_exec": "openmp",
                    "processos": 1,
                    "threads": num_threads,
                    "score_ref": ref_score,
                    "divergencias": divergencias,
                    "media_seq_total_s": avg_seq_time,
                    "media_par_s": avg_par,
                    "desvio_par_s": std_par,
                    "media_total_s": avg_total,
                    "desvio_total_s": std_total,
                    "speedup": speedup,
                    "eficiencia": eficiencia
                })

                print(f"    openmp threads={num_threads:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

            if mode == "--full-matrix" and shutil.which("mpirun"):
                if os.path.exists(mpi_bin):
                    for num_procs in mpi_processes_list:
                        print(f"  executando mpi {num_procs} processos ({repetitions}x)...")
                        par_scores = []
                        par_times = []
                        total_times = []
                        divergencias = 0

                        for rep in range(1, repetitions + 1):
                            cmd = ["mpirun", "-np", str(num_procs), mpi_bin, file_a, file_b]
                            score, t_seq, t_par, t_total, telem = run_single_execution(cmd, run_env)

                            is_correct = 1 if (ref_score is not None and score == ref_score) else 0
                            if not is_correct:
                                divergencias += 1

                            par_scores.append(score)
                            if t_par is not None:
                                par_times.append(t_par)
                            if t_total is not None:
                                total_times.append(t_total)
                            else:
                                total_times.append(telem["wall_time"])

                            detail_writer.writerow({
                                "timestamp": datetime.now().isoformat(),
                                "tipo_exec": "mpi",
                                "caso": case_rel_path,
                                "modo": mode,
                                "processos": num_procs,
                                "threads": 1,
                                "repeticao": rep,
                                "score": score,
                                "correto": is_correct,
                                "tempo_seq": t_seq,
                                "tempo_par": t_par,
                                "tempo_total": t_total,
                                "tempo_wall": telem["wall_time"],
                                "temp_start": telem["temp_start"],
                                "temp_end": telem["temp_end"],
                                "freq_start_mhz": telem["freq_start"],
                                "freq_end_mhz": telem["freq_end"],
                                "load_start": telem["load_start"],
                                "mem_start_mb": telem["mem_start_mb"],
                                "returncode": telem["returncode"]
                            })
                            detail_file.flush()

                        avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                        avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                        std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                        std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                        speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                        eficiencia = (speedup / num_procs) if num_procs > 0 else 0.0

                        if divergencias > 0:
                            print(f"    aviso: {divergencias} divergencias de score detectadas")

                        summary_records.append({
                            "caso": case_rel_path,
                            "modo": mode,
                            "tipo_exec": "mpi",
                            "processos": num_procs,
                            "threads": 1,
                            "score_ref": ref_score,
                            "divergencias": divergencias,
                            "media_seq_total_s": avg_seq_time,
                            "media_par_s": avg_par,
                            "desvio_par_s": std_par,
                            "media_total_s": avg_total,
                            "desvio_total_s": std_total,
                            "speedup": speedup,
                            "eficiencia": eficiencia
                        })

                        print(f"    mpi procs={num_procs:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

                if os.path.exists(hybrid_bin):
                    for num_procs, num_threads in hybrid_configs:
                        print(f"  executando hibrido {num_procs} processos x {num_threads} threads ({repetitions}x)...")
                        par_scores = []
                        par_times = []
                        total_times = []
                        divergencias = 0

                        for rep in range(1, repetitions + 1):
                            cmd = ["mpirun", "-np", str(num_procs), hybrid_bin, file_a, file_b, str(num_threads)]
                            score, t_seq, t_par, t_total, telem = run_single_execution(cmd, run_env)

                            is_correct = 1 if (ref_score is not None and score == ref_score) else 0
                            if not is_correct:
                                divergencias += 1

                            par_scores.append(score)
                            if t_par is not None:
                                par_times.append(t_par)
                            if t_total is not None:
                                total_times.append(t_total)
                            else:
                                total_times.append(telem["wall_time"])

                            detail_writer.writerow({
                                "timestamp": datetime.now().isoformat(),
                                "tipo_exec": "hibrido",
                                "caso": case_rel_path,
                                "modo": mode,
                                "processos": num_procs,
                                "threads": num_threads,
                                "repeticao": rep,
                                "score": score,
                                "correto": is_correct,
                                "tempo_seq": t_seq,
                                "tempo_par": t_par,
                                "tempo_total": t_total,
                                "tempo_wall": telem["wall_time"],
                                "temp_start": telem["temp_start"],
                                "temp_end": telem["temp_end"],
                                "freq_start_mhz": telem["freq_start"],
                                "freq_end_mhz": telem["freq_end"],
                                "load_start": telem["load_start"],
                                "mem_start_mb": telem["mem_start_mb"],
                                "returncode": telem["returncode"]
                            })
                            detail_file.flush()

                        avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                        avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                        std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                        std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                        total_workers = num_procs * num_threads
                        speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                        eficiencia = (speedup / total_workers) if total_workers > 0 else 0.0

                        if divergencias > 0:
                            print(f"    aviso: {divergencias} divergencias de score detectadas")

                        summary_records.append({
                            "caso": case_rel_path,
                            "modo": mode,
                            "tipo_exec": "hibrido",
                            "processos": num_procs,
                            "threads": num_threads,
                            "score_ref": ref_score,
                            "divergencias": divergencias,
                            "media_seq_total_s": avg_seq_time,
                            "media_par_s": avg_par,
                            "desvio_par_s": std_par,
                            "media_total_s": avg_total,
                            "desvio_total_s": std_total,
                            "speedup": speedup,
                            "eficiencia": eficiencia
                        })

                        print(f"    hibrido procs={num_procs:2d}, threads={num_threads:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

    detail_file.close()

    summary_fieldnames = [
        "caso", "modo", "tipo_exec", "processos", "threads", "score_ref", "divergencias",
        "media_seq_total_s", "media_par_s", "desvio_par_s",
        "media_total_s", "desvio_total_s", "speedup", "eficiencia"
    ]

    with open(csv_summary_path, "w", newline="") as sf:
        swriter = csv.DictWriter(sf, fieldnames=summary_fieldnames)
        swriter.writeheader()
        for r in summary_records:
            swriter.writerow(r)

    print("experimento finalizado")
    print(f"sumario em: {csv_summary_path}")

if __name__ == "__main__":
    main()
