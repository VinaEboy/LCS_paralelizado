# teste mais curto, que serve para teste de sanidade
# e que justifica o BLOCK_SIZE = 512, melhor speedup encontrado empiricamente

import os
import sys
import shutil
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from utils_experiment import (
    collect_system_metadata,
    save_system_metadata_csv,
    ensure_binaries,
    ensure_inputs,
    run_single_execution,
    ResultManager,
    BlockSizeManager
)

script_dir = os.path.dirname(os.path.abspath(__file__))
lcs_dir = os.path.abspath(os.path.join(script_dir, ".."))
inputs_dir = os.path.join(lcs_dir, "inputs")
results_dir = os.path.join(lcs_dir, "resultados", "testes")

seq_bin = os.path.join(lcs_dir, "lcs_seq")
omp_bin = os.path.join(lcs_dir, "lcs_omp")
mpi_bin = os.path.join(lcs_dir, "lcs_mpi")
hybrid_bin = os.path.join(lcs_dir, "lcs_hybrid")

threads_list = [1, 2, 4, 8, 16]
mpi_processes_list = [1, 2, 4, 8, 16]
hybrid_configs = [(2, 2), (2, 4), (4, 2), (2, 8), (4, 4), (8, 2)]
repetitions = 3

test_cases = [
    ("small", "Q2/Q2_p1", ["--full-matrix", "--mem-opt"]),
    ("small", "Q4/Q4_p1", ["--full-matrix", "--mem-opt"]),
    ("big",   "Q5/Q5_random", ["--mem-opt"]),  # valida matriz 80k com u32 sem overflow
]

# Casos para a varredura de BLOCK_SIZE
block_size_candidates = [64, 128, 256, 512]
block_size_cases = [
    ("small", "Q4/Q4_random", ["--full-matrix", "--mem-opt"], [4, 8, 16]),
    ("big",   "Q5/Q5_random", ["--mem-opt"], [8, 16]),
]

def main():
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    current_mtype_mode = None
    ensure_inputs(script_dir)

    os.makedirs(results_dir, exist_ok=True)

    # grava metadados do ambiente na raiz da saida de testes
    env_info = collect_system_metadata()
    env_info_path = os.path.join(results_dir, "ambiente_info.csv")
    save_system_metadata_csv(env_info_path, env_info)
    print(f"metadados do ambiente salvos em: {env_info_path}")

    run_env = os.environ.copy()
    run_env["OMP_PROC_BIND"] = "close"
    run_env["OMP_PLACES"] = "cores"

    detail_fieldnames = [
        "timestamp", "tipo_exec", "caso", "modo", "processos", "threads", "block_size", "repeticao",
        "score", "tipo_dado", "correto", "tempo_seq", "tempo_par", "tempo_total", "tempo_wall",
        "temp_start", "temp_end", "freq_start_mhz", "freq_end_mhz", "load_start", "mem_start_mb",
        "returncode"
    ]

    summary_fieldnames = [
        "caso", "modo", "tipo_exec", "processos", "threads", "block_size", "score_ref",
        "media_seq_total_s", "media_par_s", "desvio_par_s",
        "media_total_s", "desvio_total_s", "speedup", "eficiencia"
    ]

    res_mgr = ResultManager(results_dir, detail_fieldnames, summary_fieldnames)

    has_mpirun = shutil.which("mpirun") is not None

    for cat, case_rel_path, allowed_modes in test_cases:
        case_full_path = os.path.join(inputs_dir, cat, case_rel_path)
        file_a = os.path.join(case_full_path, "fileA.in")
        file_b = os.path.join(case_full_path, "fileB.in")

        if not os.path.exists(file_a) or not os.path.exists(file_b):
            print(f"aviso: arquivos para o caso {case_rel_path} nao encontrados em {case_full_path}, pulando")
            continue

        family = case_rel_path.split("/")[0]

        needed_mode = "u32" if ((cat == "big" and ("Q5" in case_rel_path or "Q6" in case_rel_path)) or cat == "giga") else "u16"
        if current_mtype_mode != needed_mode:
            print(f"\n>>> Recompilando binarios para modo {needed_mode}...")
            ensure_binaries(lcs_dir, needed_mode)
            current_mtype_mode = needed_mode

        print(f"==================================================")
        print(f"caso: {case_rel_path}")
        print(f"==================================================")

        for mode in allowed_modes:
            print(f"\nexecutando sequencial para {case_rel_path} [{mode}] ({repetitions}x)...")
            seq_scores = []
            seq_totals = []
            tipo_dado_ref = None

            for rep in range(1, repetitions + 1):
                cmd = [seq_bin, file_a, file_b, mode]
                score, t_seq, _, t_total, telem = run_single_execution(cmd, run_env)

                seq_scores.append(score)
                tipo_dado_ref = telem.get("tipo")
                if t_total is not None:
                    seq_totals.append(t_total)
                else:
                    seq_totals.append(telem["wall_time"])

                res_mgr.log_detail(family, {
                    "timestamp": datetime.now().isoformat(),
                    "tipo_exec": "sequencial",
                    "caso": case_rel_path,
                    "modo": mode,
                    "processos": 1,
                    "threads": 1,
                    "block_size": "-",
                    "repeticao": rep,
                    "score": score,
                    "tipo_dado": tipo_dado_ref,
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

            ref_score = seq_scores[0] if seq_scores else None
            avg_seq_time = sum(seq_totals) / len(seq_totals) if seq_totals else 0.0
            print(f"  sequencial concluido: media={avg_seq_time:.4f}s, score_ref={ref_score}, tipo={tipo_dado_ref}")

            # OpenMP (usando default 512)
            for num_threads in threads_list:
                print(f"  executando openmp {num_threads} threads [{mode}] ({repetitions}x)...")
                par_scores = []
                par_times = []
                total_times = []
                divergencias = 0

                for rep in range(1, repetitions + 1):
                    cmd = [omp_bin, file_a, file_b, str(num_threads), mode, "--block-size", "512"]
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

                    res_mgr.log_detail(family, {
                        "timestamp": datetime.now().isoformat(),
                        "tipo_exec": "openmp",
                        "caso": case_rel_path,
                        "modo": mode,
                        "processos": 1,
                        "threads": num_threads,
                        "block_size": 512,
                        "repeticao": rep,
                        "score": score,
                        "tipo_dado": telem.get("tipo"),
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

                avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                eficiencia = (speedup / num_threads) if num_threads > 0 else 0.0

                if divergencias > 0:
                    print(f"    aviso: {divergencias} divergencias de score detectadas")

                res_mgr.log_summary(family, {
                    "caso": case_rel_path,
                    "modo": mode,
                    "tipo_exec": "openmp",
                    "processos": 1,
                    "threads": num_threads,
                    "block_size": 512,
                    "score_ref": ref_score,
                    "media_seq_total_s": avg_seq_time,
                    "media_par_s": avg_par,
                    "desvio_par_s": std_par,
                    "media_total_s": avg_total,
                    "desvio_total_s": std_total,
                    "speedup": speedup,
                    "eficiencia": eficiencia
                })

                print(f"    openmp threads={num_threads:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

            # MPI puro (tanto --full-matrix quanto --mem-opt)
            if has_mpirun and os.path.exists(mpi_bin):
                for num_procs in mpi_processes_list:
                    print(f"  executando mpi {num_procs} processos [{mode}] ({repetitions}x)...")
                    par_scores = []
                    par_times = []
                    total_times = []
                    divergencias = 0

                    for rep in range(1, repetitions + 1):
                        cmd = ["mpirun", "--mca", "btl", "^tcp", "-np", str(num_procs), mpi_bin, file_a, file_b, mode]
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

                        res_mgr.log_detail(family, {
                            "timestamp": datetime.now().isoformat(),
                            "tipo_exec": "mpi",
                            "caso": case_rel_path,
                            "modo": mode,
                            "processos": num_procs,
                            "threads": 1,
                            "block_size": "-",
                            "repeticao": rep,
                            "score": score,
                            "tipo_dado": telem.get("tipo"),
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

                    avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                    avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                    std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                    std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                    speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                    eficiencia = (speedup / num_procs) if num_procs > 0 else 0.0

                    if divergencias > 0:
                        print(f"    aviso: {divergencias} divergencias de score detectadas")

                    res_mgr.log_summary(family, {
                        "caso": case_rel_path,
                        "modo": mode,
                        "tipo_exec": "mpi",
                        "processos": num_procs,
                        "threads": 1,
                        "block_size": "-",
                        "score_ref": ref_score,
                        "media_seq_total_s": avg_seq_time,
                        "media_par_s": avg_par,
                        "desvio_par_s": std_par,
                        "media_total_s": avg_total,
                        "desvio_total_s": std_total,
                        "speedup": speedup,
                        "eficiencia": eficiencia
                    })

                    print(f"    mpi procs={num_procs:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

            # Hibrido MPI + OpenMP
            if has_mpirun and os.path.exists(hybrid_bin):
                for num_procs, num_threads in hybrid_configs:
                    print(f"  executando hibrido {num_procs} processos x {num_threads} threads [{mode}] ({repetitions}x)...")
                    par_scores = []
                    par_times = []
                    total_times = []
                    divergencias = 0

                    for rep in range(1, repetitions + 1):
                        cmd = [
                            "mpirun", "--mca", "btl", "^tcp", "-np", str(num_procs),
                            hybrid_bin, file_a, file_b, str(num_threads), mode, "--block-size", "512"
                        ]
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

                        res_mgr.log_detail(family, {
                            "timestamp": datetime.now().isoformat(),
                            "tipo_exec": "hibrido",
                            "caso": case_rel_path,
                            "modo": mode,
                            "processos": num_procs,
                            "threads": num_threads,
                            "block_size": 512,
                            "repeticao": rep,
                            "score": score,
                            "tipo_dado": telem.get("tipo"),
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

                    avg_par = sum(par_times) / len(par_times) if par_times else 0.0
                    avg_total = sum(total_times) / len(total_times) if total_times else 0.0
                    std_par = (sum((x - avg_par) ** 2 for x in par_times) / len(par_times)) ** 0.5 if len(par_times) > 1 else 0.0
                    std_total = (sum((x - avg_total) ** 2 for x in total_times) / len(total_times)) ** 0.5 if len(total_times) > 1 else 0.0

                    total_workers = num_procs * num_threads
                    speedup = (avg_seq_time / avg_total) if avg_total > 0.0 else 0.0
                    eficiencia = (speedup / total_workers) if total_workers > 0 else 0.0

                    if divergencias > 0:
                        print(f"    aviso: {divergencias} divergencias de score detectadas")

                    res_mgr.log_summary(family, {
                        "caso": case_rel_path,
                        "modo": mode,
                        "tipo_exec": "hibrido",
                        "processos": num_procs,
                        "threads": num_threads,
                        "block_size": 512,
                        "score_ref": ref_score,
                        "media_seq_total_s": avg_seq_time,
                        "media_par_s": avg_par,
                        "desvio_par_s": std_par,
                        "media_total_s": avg_total,
                        "desvio_total_s": std_total,
                        "speedup": speedup,
                        "eficiencia": eficiencia
                    })

                    print(f"    hibrido procs={num_procs:2d}, threads={num_threads:2d}: tempo_medio={avg_total:.4f}s (std={std_total:.4f}), speedup={speedup:.2f}, ef={eficiencia:.2f}")

    res_mgr.close()

    print("\n" + "=" * 60)
    print("PARTE 2: VARREDURA DE BLOCK_SIZE (64, 128, 256, 512)")
    print("=" * 60)

    bs_fields = [
        "caso", "modo", "block_size", "threads", "score_ref",
        "media_seq_s", "media_total_s", "desvio_total_s", "speedup"
    ]
    bs_mgr = BlockSizeManager(results_dir, bs_fields)

    for cat, case, modes, th_list in block_size_cases:
        fa = os.path.join(inputs_dir, cat, case, "fileA.in")
        fb = os.path.join(inputs_dir, cat, case, "fileB.in")
        if not (os.path.exists(fa) and os.path.exists(fb)):
            print(f"aviso: caso {case} nao encontrado, pulando")
            continue

        bs_family = case.split("/")[0]

        needed_mode = "u32" if ((cat == "big" and ("Q5" in case or "Q6" in case)) or cat == "giga") else "u16"
        if current_mtype_mode != needed_mode:
            print(f"\n>>> Recompilando binarios para modo {needed_mode}...")
            ensure_binaries(lcs_dir, needed_mode)
            current_mtype_mode = needed_mode

        for mode in modes:
            # Mede sequencial
            seq_times = []
            ref = None
            for _ in range(repetitions):
                sc, _, _, tt, tel = run_single_execution([seq_bin, fa, fb, mode], run_env)
                ref = sc if ref is None else ref
                seq_times.append(tt if tt is not None else tel["wall_time"])
            avg_seq = sum(seq_times) / len(seq_times)
            print(f"\n[Varredura BS] {case} [{mode}] seq_medio={avg_seq:.4f}s ref_score={ref}")

            for nt in th_list:
                line_str = f"  threads={nt:2d} |"
                for bs in block_size_candidates:
                    tot_times = []
                    divs = 0
                    for _ in range(repetitions):
                        cmd = [omp_bin, fa, fb, str(nt), mode, "--block-size", str(bs)]
                        sc, _, _, tt, tel = run_single_execution(cmd, run_env)
                        if sc != ref:
                            divs += 1
                        tot_times.append(tt if tt is not None else tel["wall_time"])
                    avg_bs = sum(tot_times) / len(tot_times)
                    std_bs = (sum((x - avg_bs) ** 2 for x in tot_times) / len(tot_times)) ** 0.5
                    sp_bs = avg_seq / avg_bs if avg_bs > 0 else 0.0

                    bs_mgr.log_bs(bs_family, {
                        "caso": case,
                        "modo": mode,
                        "block_size": bs,
                        "threads": nt,
                        "score_ref": ref,
                        "media_seq_s": avg_seq,
                        "media_total_s": avg_bs,
                        "desvio_total_s": std_bs,
                        "speedup": sp_bs
                    })

                    flag = "!" if divs else ""
                    line_str += f" bs{bs}={avg_bs:.3f}s({sp_bs:.2f}x){flag}"
                print(line_str)

    bs_mgr.close()

    print("\n" + "=" * 60)
    print("TESTE COMPLETO FINALIZADO COM SUCESSO!")
    print(f"Ambiente info:      {env_info_path}")
    print(f"Resumo geral:       {res_mgr.global_sum_path}")
    print(f"Detalhado geral:    {res_mgr.global_detail_path}")
    print(f"Pastas por exemplo: {results_dir}/<Q2, Q4, Q5...>/[sumarizado.csv, detalhado.csv]")
    print(f"Varredura de bloco: {bs_mgr.global_path} e nas pastas de exemplo")
    print("=" * 60)

if __name__ == "__main__":
    main()
