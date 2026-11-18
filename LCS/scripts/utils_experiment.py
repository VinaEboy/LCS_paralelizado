import os
import sys
import glob
import time
import subprocess
import json
import platform
import shutil

# funcoes de telemetria e metadados do hardware

def collect_system_metadata():
    meta = {}
    meta["sistema_operacional"] = platform.platform()
    meta["kernel_release"] = platform.release()
    meta["arquitetura"] = platform.machine()

    # processador
    try:
        res = subprocess.run(["lscpu"], capture_output=True, text=True)
        meta["lscpu"] = res.stdout.strip()
    except Exception:
        meta["lscpu"] = "indisponivel"

    # versao gcc
    try:
        res = subprocess.run(["gcc", "--version"], capture_output=True, text=True)
        meta["gcc_version"] = res.stdout.splitlines()[0]
    except Exception:
        meta["gcc_version"] = "indisponivel"

    # status turbo boost
    try:
        with open("/sys/devices/system/cpu/cpufreq/boost", "r") as f:
            meta["turbo_boost_ativo"] = (f.read().strip() == "1")
    except Exception:
        meta["turbo_boost_ativo"] = "desconhecido"

    # governor de desempenho
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
            meta["cpu_governor"] = f.read().strip()
    except Exception:
        meta["cpu_governor"] = "desconhecido"

    meta["openmp_pinning"] = {
        "OMP_PROC_BIND": os.environ.get("OMP_PROC_BIND", "close"),
        "OMP_PLACES": os.environ.get("OMP_PLACES", "cores")
    }

    return meta

def get_cpu_temp():
    try:
        for temp_path in glob.glob("/sys/class/hwmon/hwmon*/temp*_input"):
            with open(temp_path, "r") as f:
                val = float(f.read().strip()) / 1000.0
                if 20.0 <= val <= 110.0:
                    return val
    except Exception:
        pass
    return -1.0

def get_cpu_freq_mhz():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        pass
    return -1.0

def get_load_avg_1m():
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            return float(parts[0])
    except Exception:
        pass
    return -1.0

def get_mem_available_mb():
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    parts = line.split()
                    return float(parts[1]) / 1024.0
    except Exception:
        pass
    return -1.0

# parser da saida dos programas lcs
def parse_lcs_output(output_str):
    score = None
    t_seq = None
    t_par = None
    t_total = None

    for line in output_str.splitlines():
        line = line.strip()
        if line.startswith("Score:"):
            try:
                score = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Tempo sequencial:"):
            try:
                t_seq = float(line.split(":")[1].replace("s", "").strip())
            except ValueError:
                pass
        elif line.startswith("Tempo paralelo:"):
            try:
                t_par = float(line.split(":")[1].replace("s", "").strip())
            except ValueError:
                pass
        elif line.startswith("Tempo total:"):
            try:
                t_total = float(line.split(":")[1].replace("s", "").strip())
            except ValueError:
                pass

    return score, t_seq, t_par, t_total

def ensure_binaries(lcs_dir):
    print("compilando os binarios")
    targets = ["seq", "omp"]
    if shutil.which("mpicc"):
        targets.extend(["mpi", "hybrid"])
    cmd = ["make", "-C", lcs_dir] + targets
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("erro ao compilar:")
        print(res.stderr)
        sys.exit(1)

def ensure_inputs(script_dir):
    print("gerando/verificando arquivos de entrada")
    cmd = ["python3", os.path.join(script_dir, "generate_input.py")]
    subprocess.run(cmd, check=True)

def run_single_execution(cmd, env):
    temp_start = get_cpu_temp()
    freq_start = get_cpu_freq_mhz()
    load_start = get_load_avg_1m()
    mem_start = get_mem_available_mb()

    start_wall = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    end_wall = time.time()

    temp_end = get_cpu_temp()
    freq_end = get_cpu_freq_mhz()
    elapsed_wall = end_wall - start_wall

    score, t_seq, t_par, t_total = parse_lcs_output(res.stdout)

    telemetry = {
        "wall_time": elapsed_wall,
        "temp_start": temp_start,
        "temp_end": temp_end,
        "freq_start": freq_start,
        "freq_end": freq_end,
        "load_start": load_start,
        "mem_start_mb": mem_start,
        "returncode": res.returncode,
        "stderr": res.stderr.strip()
    }

    return score, t_seq, t_par, t_total, telemetry
