import os
import sys
import glob
import time
import subprocess
import csv
import platform
import shutil

# Adiciona o ambiente conda lcs-mpi ao PATH se existir e o mpicc nao estiver no PATH padrao
conda_mpi_bin = os.path.expanduser("~/miniconda3/envs/lcs-mpi/bin")
if os.path.exists(conda_mpi_bin) and not shutil.which("mpicc"):
    os.environ["PATH"] = conda_mpi_bin + ":" + os.environ.get("PATH", "")
os.environ.setdefault("OMPI_CC", "gcc")

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

def save_system_metadata_csv(filepath, meta):
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metrica", "valor"])
        for k, v in meta.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    writer.writerow([f"{k}.{subk}", str(subv)])
            else:
                writer.writerow([k, str(v)])

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
    tipo = None
    block_size = None
    chunk_size = None

    for line in output_str.splitlines():
        line = line.strip()
        if line.startswith("Score:"):
            try:
                score = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Tipo:"):
            tipo = line.split(":")[1].strip()
        elif line.startswith("Block size:"):
            try:
                block_size = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("Chunk size:"):
            try:
                chunk_size = int(line.split(":")[1].strip())
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

    return score, t_seq, t_par, t_total, tipo, block_size, chunk_size

def ensure_binaries(lcs_dir, mtype_mode="u16"):
    print(f"compilando os binarios ({mtype_mode})")
    target = "u32" if mtype_mode == "u32" else "u16"
    cmd = ["make", "-C", lcs_dir, target]
    env = os.environ.copy()
    env["OMPI_CC"] = "gcc"
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
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

    score, t_seq, t_par, t_total, tipo, block_size, chunk_size = parse_lcs_output(res.stdout)

    telemetry = {
        "wall_time": elapsed_wall,
        "temp_start": temp_start,
        "temp_end": temp_end,
        "freq_start": freq_start,
        "freq_end": freq_end,
        "load_start": load_start,
        "mem_start_mb": mem_start,
        "returncode": res.returncode,
        "stderr": res.stderr.strip(),
        "tipo": tipo,
        "block_size": block_size,
        "chunk_size": chunk_size
    }

    return score, t_seq, t_par, t_total, telemetry

class ResultManager:
    def __init__(self, root_dir, detail_fields, summary_fields):
        self.root_dir = root_dir
        self.detail_fields = detail_fields
        self.summary_fields = summary_fields
        self.family_files = {}

        os.makedirs(root_dir, exist_ok=True)
        self.global_detail_path = os.path.join(root_dir, "detalhado_geral.csv")
        self.global_sum_path = os.path.join(root_dir, "sumarizado_geral.csv")
        
        self.global_detail_f = open(self.global_detail_path, "w", newline="")
        self.global_detail_w = csv.DictWriter(self.global_detail_f, fieldnames=detail_fields)
        self.global_detail_w.writeheader()
        self.global_detail_f.flush()

        self.global_sum_f = open(self.global_sum_path, "w", newline="")
        self.global_sum_w = csv.DictWriter(self.global_sum_f, fieldnames=summary_fields)
        self.global_sum_w.writeheader()
        self.global_sum_f.flush()

    def get_family_writers(self, family):
        if family not in self.family_files:
            fam_dir = os.path.join(self.root_dir, family)
            os.makedirs(fam_dir, exist_ok=True)
            
            df = open(os.path.join(fam_dir, "detalhado.csv"), "w", newline="")
            dw = csv.DictWriter(df, fieldnames=self.detail_fields)
            dw.writeheader()
            df.flush()

            sf = open(os.path.join(fam_dir, "sumarizado.csv"), "w", newline="")
            sw = csv.DictWriter(sf, fieldnames=self.summary_fields)
            sw.writeheader()
            sf.flush()

            self.family_files[family] = {
                'detail_f': df, 'detail_w': dw,
                'sum_f': sf, 'sum_w': sw
            }
        return self.family_files[family]

    def log_detail(self, family, record):
        fw = self.get_family_writers(family)
        fw['detail_w'].writerow(record)
        fw['detail_f'].flush()
        self.global_detail_w.writerow(record)
        self.global_detail_f.flush()

    def log_summary(self, family, record):
        fw = self.get_family_writers(family)
        fw['sum_w'].writerow(record)
        fw['sum_f'].flush()
        self.global_sum_w.writerow(record)
        self.global_sum_f.flush()

    def close(self):
        for fdict in self.family_files.values():
            fdict['detail_f'].close()
            fdict['sum_f'].close()
        self.global_detail_f.close()
        self.global_sum_f.close()

class BlockSizeManager:
    def __init__(self, root_dir, bs_fields):
        self.root_dir = root_dir
        self.bs_fields = bs_fields
        self.family_files = {}

        os.makedirs(root_dir, exist_ok=True)
        self.global_path = os.path.join(root_dir, "block_size_geral.csv")
        self.global_f = open(self.global_path, "w", newline="")
        self.global_w = csv.DictWriter(self.global_f, fieldnames=bs_fields)
        self.global_w.writeheader()
        self.global_f.flush()

    def log_bs(self, family, record):
        if family not in self.family_files:
            fam_dir = os.path.join(self.root_dir, family)
            os.makedirs(fam_dir, exist_ok=True)
            bf = open(os.path.join(fam_dir, "block_size.csv"), "w", newline="")
            bw = csv.DictWriter(bf, fieldnames=self.bs_fields)
            bw.writeheader()
            bf.flush()
            self.family_files[family] = {'f': bf, 'w': bw}

        fw = self.family_files[family]
        fw['w'].writerow(record)
        fw['f'].flush()
        self.global_w.writerow(record)
        self.global_f.flush()

    def close(self):
        for fdict in self.family_files.values():
            fdict['f'].close()
        self.global_f.close()

