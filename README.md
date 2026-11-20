# Paralelização do Algoritmo LCS (OpenMP + MPI)

Trabalho prático da disciplina de **Programação Paralela (CI1316)**  
Departamento de Informática (DINF) — Universidade Federal do Paraná (UFPR)  
Professor: **Marco Antonio Zanata Alves**

---

## Integrantes
* **Gabriel Henrique Polo** — GRR20241558
* **Vinícius Gregorio Fucci** — GRR20241272

---

## Resumo do Trabalho
O objetivo deste trabalho é implementar, analisar e otimizar o algoritmo da **Maior Subsequência Comum (Longest Common Subsequence — LCS)** utilizando técnicas de programação paralela em memória compartilhada (OpenMP) e distribuída (MPI), além de uma abordagem híbrida (MPI + OpenMP).

### Arquitetura das Implementações:
1. **Sequencial (`lcs_seq`):**
   - Versão padrão preenchendo toda a matriz de programação dinâmica $\mathcal{O}(M \times N)$.
   - Versão com otimização de memória (`--mem-opt`) utilizando apenas 2 linhas ativas, reduzindo o consumo de memória para $\mathcal{O}(N)$.

2. **OpenMP (`lcs_omp`):**
   - Decomposição em blocos 2D (*tiling*) de tamanho configurável (`--block-size N`, padrão `512`).
   - Sincronização e avanço da frente de onda (*wavefront*) via grafo de tarefas do OpenMP com dependências de dados (`#pragma omp task depend(in: ...) depend(out: ...)`).
   - Otimização de memória (`--mem-opt`) armazenando apenas as bordas ativas (superior e esquerda) de cada bloco, permitindo resolver matrizes gigantescas com espaço proporcional a $\mathcal{O}(N_{blocos})$.

3. **MPI (`lcs_mpi`):**
   - Decomposição de domínio 1D por faixas horizontais de linhas de $seqB$ entre os processos MPI.
   - Comunicação assíncrona/pipeline em blocos de colunas (`--chunk-size N`, padrão `1024`), onde cada processo calcula seu bloco e despacha a última linha para o processo vizinho abaixo.
   - Otimização de memória (`--mem-opt`) que armazena apenas buffers de 1 linha local e a borda do chunk.

4. **Híbrido MPI + OpenMP (`lcs_hybrid`):**
   - Combina a decomposição 1D do MPI entre nós/processos com o paralelismo de tarefas 2D do OpenMP dentro da faixa de cada processo.
   - Suporte completo tanto a matriz completa quanto ao modo `--mem-opt`.

5. **Suporte Dual-Type (16 bits vs 32 bits):**
   - Por padrão, matrizes são alocadas com `uint16_t` (`mtype`, alvo `make u16`), economizando 50% de RAM e tráfego de cache.
   - Para entradas de grande porte com pontuação acima de 65.535 (como Q5, Q6 e entradas da categoria `giga`), o código suporta `uint32_t` via compilação com a flag `-DMTYPE_32` (alvo `make u32`), sem perigo de *overflow*.

---

## Estrutura do Repositório

```text
.
├── Enunciado Trabalho1 OpenMP_MPI.pdf
├── Relatório_Paralela.pdf
├── README.md
└── LCS/
    ├── Makefile
    ├── include/
    │   ├── macros.h         # Definicoes de tipos (mtype 16/32 bits), constantes e defaults
    │   ├── utils.h          # Leitura de sequencias, alocacao e operacoes basicas
    │   ├── utils_omp.h      # Declaracoes das rotinas de regiao/chunk e mem-opt OpenMP
    │   └── utils_mpi.h      # Declaracoes de inicializacao e pipelines MPI e Hibrido
    ├── src/
    │   ├── lcs_seq.c        # Ponto de entrada sequencial
    │   ├── lcs_omp.c        # Ponto de entrada OpenMP
    │   ├── lcs_mpi.c        # Ponto de entrada MPI
    │   ├── lcs_hybrid.c     # Ponto de entrada Hibrido (MPI + OpenMP)
    │   └── utils/
    │       ├── utils.c      # Implementacao basica e I/O
    │       ├── utils_omp.c  # Kernel de tarefas e mem-opt OpenMP
    │       └── utils_mpi.c  # Pipeline MPI e Hibrido
    ├── scripts/
    │   ├── generate_input.py   # Gerador de entradas deterministicas
    │   ├── utils_experiment.py # Helpers de compilacao, telemetria e execucao
    │   ├── run_test.py         # Script de teste/sanidade e varredura de BLOCK_SIZE
    │   └── run_experiment.py   # Bateria completa oficial do experimento
    ├── inputs/                 # Entradas geradas (small, big, giga)
    └── resultados/             # Armazenamento organizado dos resultados (somente CSV)
        ├── testes/             # CSVs gerados pelo run_test.py
        └── experimentos/       # CSVs gerados pelo run_experiment.py
```

---

## Requisitos e Ambiente

* **Compilador C:** `gcc` (suporte a C99/C11 e OpenMP `-fopenmp`).
* **MPI:** OpenMPI 5.x ou compatível com suporte a threads (`MPI_THREAD_FUNNELED`).
* **Python:** Python 3.8+ para os scripts automatizados.

### Configuração com Conda no cluster/máquina `duo`:
Se a máquina não tiver OpenMPI instalado no sistema global, utilize o ambiente Conda preparado:
```bash
# ativando o ambiente ou garantindo no PATH
export PATH=~/miniconda3/envs/lcs-mpi/bin:$PATH
export OMPI_CC=gcc
```

---

## Como Compilar

Dentro do diretório `LCS`:

```bash
cd LCS

# compilar versao padrao de 16 bits (u16)
make u16

# compilar versao estendida de 32 bits para matrizes gigantes (u32)
make u32

# compilar alvos individuais
make seq
make omp
make mpi
make hybrid

# limpeza
make clean
```

---

## Execução Individual dos Binários

### 1. Sequencial (`lcs_seq`)
```bash
./lcs_seq <fileA.in> <fileB.in> [--mem-opt | --full-matrix] [--debug-matrix]
```
Exemplo:
```bash
./lcs_seq inputs/small/Q1/Q1_p1/fileA.in inputs/small/Q1/Q1_p1/fileB.in --mem-opt
```

### 2. OpenMP (`lcs_omp`)
```bash
./lcs_omp <fileA.in> <fileB.in> [threads] [--mem-opt | --full-matrix] [--block-size N] [--debug-matrix]
```
Exemplo:
```bash
./lcs_omp inputs/small/Q3/Q3_p1/fileA.in inputs/small/Q3/Q3_p1/fileB.in 8 --mem-opt --block-size 512
```

### 3. MPI (`lcs_mpi`)
```bash
mpirun [opcoes_mpi] -np <processos> ./lcs_mpi <fileA.in> <fileB.in> [--mem-opt | --full-matrix] [--chunk-size N]
```
Exemplo com 4 processos:
```bash
mpirun --mca btl ^tcp -np 4 ./lcs_mpi inputs/small/Q2/Q2_p1/fileA.in inputs/small/Q2/Q2_p1/fileB.in --mem-opt
```

### 4. Híbrido MPI + OpenMP (`lcs_hybrid`)
```bash
mpirun [opcoes_mpi] -np <processos> ./lcs_hybrid <fileA.in> <fileB.in> [threads] [--mem-opt | --full-matrix] [--block-size N] [--chunk-size N]
```
Exemplo com 2 processos e 4 threads por processo:
```bash
mpirun --mca btl ^tcp -np 2 ./lcs_hybrid inputs/small/Q2/Q2_p1/fileA.in inputs/small/Q2/Q2_p1/fileB.in 4 --mem-opt --block-size 512
```

---

## Execução dos Scripts Automatizados

Todos os scripts geram **exclusivamente arquivos `.csv`** (sem arquivos `.json`), organizados automaticamente em subdiretórios categorizados por exemplo/família dentro de `LCS/resultados/`.

### 1. Script de Teste e Validação de `BLOCK_SIZE` (`run_test.py`)
Executa um teste de sanidade rápido cobrindo casos representativos (`Q2`, `Q4` e `Q5`), realizando a recompilação automática entre `u16` e `u32`. Em seguida, executa a **Varredura de BLOCK_SIZE** (testando `64`, `128`, `256` e `512` em `Q4` e `Q5`) para validar empiricamente a escolha de `BLOCK_SIZE = 512`.

```bash
cd LCS
python3 scripts/run_test.py
```

Os resultados são salvos em `LCS/resultados/testes/`:
* `ambiente_info.csv`: Metadados do processador, frequências, kernel e versões do compilador `gcc` e OpenMPI.
* `sumarizado_geral.csv`: Visão consolidada de todos os casos testados com métricas de tempo, speedup e eficiência.
* `detalhado_geral.csv`: Log consolidado de todas as repetições individuais com dados de telemetria.
* `block_size_geral.csv`: Tabela consolidada de speedup para cada valor de `block_size` testado com diferentes contagens de threads.
* `<exemplo>/` (ex: `Q2/`, `Q4/`, `Q5/`): Subpastas individuais por família contendo:
  - `sumarizado.csv`: Resultados médios e métricas da família correspondente.
  - `detalhado.csv`: Repetições detalhadas com telemetria daquela família.
  - `block_size.csv`: Varredura de tamanhos de bloco para a família (quando aplicável).

### 2. Script do Experimento Principal Oficial (`run_experiment.py`)
Bateria de testes completa contendo todas as entradas (`small`, `big`, `giga`), abrangendo matrizes quadradas e retangulares (diretas e invertidas) sob todos os padrões de caracteres (`p1` a `p4` e `random`), com **20 repetições por configuração**.

Como a bateria completa pode levar algumas horas, execute em background com `nohup`:

```bash
cd LCS
nohup python3 scripts/run_experiment.py > experimento.log 2>&1 &
```

Para acompanhar o progresso em tempo real:
```bash
tail -f experimento.log
```

Os resultados são salvos em `LCS/resultados/experimentos/`:
* `ambiente_info.csv`: Metadados da máquina de teste na raiz do diretório.
* `sumarizado_geral.csv`: Tabela geral consolidada com todas as configurações testadas.
* `detalhado_geral.csv`: Registro geral consolidado de todas as repetições individuais com telemetria.
* `<exemplo>/` (ex: `Q1/`, `Q2/`, `R1/`, `enunciado/`, etc.): Pastas organizadas por exemplo/família contendo:
  - `sumarizado.csv`: Tabela com médias, desvios padrões, speedup e eficiência daquele exemplo.
  - `detalhado.csv`: Registro de todas as repetições daquele exemplo.

---

## Estrutura de Diretórios dos Resultados

```text
LCS/resultados/
├── testes/
│   ├── ambiente_info.csv
│   ├── sumarizado_geral.csv
│   ├── detalhado_geral.csv
│   ├── block_size_geral.csv
│   ├── Q2/
│   │   ├── sumarizado.csv
│   │   └── detalhado.csv
│   ├── Q4/
│   │   ├── sumarizado.csv
│   │   ├── detalhado.csv
│   │   └── block_size.csv
│   └── Q5/
│       ├── sumarizado.csv
│       ├── detalhado.csv
│       └── block_size.csv
│
└── experimentos/
    ├── ambiente_info.csv
    ├── sumarizado_geral.csv
    ├── detalhado_geral.csv
    ├── Q1/
    │   ├── sumarizado.csv
    │   └── detalhado.csv
    ├── Q2/
    │   ├── sumarizado.csv
    │   └── detalhado.csv
    └── ... (uma pasta para cada família de entrada: Q1-Q8, R1-R6, etc.)
```

---

## Explicação das Saídas e Colunas dos CSVs

### Saída no Terminal (Console Log)
Durante a execução, o terminal exibe o progresso em tempo real:
* **Caso e Modo:** Qual arquivo de entrada e se está executando em `--full-matrix` ou `--mem-opt`.
* **Sequencial:** Tempo médio de referência e score obtido.
* **Variantes Paralelas:** Para cada número de threads ou processos, exibe:
  - `tempo_medio`: Média aritmética do tempo de execução total (em segundos).
  - `std`: Desvio padrão amostral das repetições.
  - `speedup`: Aceleração em relação ao tempo sequencial ($S = T_{seq} / T_{par}$).
  - `ef`: Eficiência paralela em relação aos núcleos alocados ($E = S / P$).
* **Avisos de Divergência:** Se qualquer execução paralela produzir um score diferente do sequencial, um alerta com o score divergente é impresso no console.

### Colunas dos Arquivos CSV

#### 1. `sumarizado.csv` e `sumarizado_geral.csv`
| Coluna | Descrição |
| :--- | :--- |
| `caso` | Identificador do caso de teste (ex: `Q2/Q2_p1`, `Q5/Q5_random`) |
| `modo` | `--full-matrix` (matriz completa) ou `--mem-opt` (otimizado em memória) |
| `tipo_exec` | Tipo do paralelismo: `sequencial`, `openmp`, `mpi` ou `hibrido` |
| `processos` | Quantidade de processos MPI utilizados (1 para sequencial e OpenMP) |
| `threads` | Quantidade de threads OpenMP por processo (1 para sequencial e MPI puro) |
| `block_size` | Tamanho do bloco utilizado nas tarefas OpenMP (padrão `512`) |
| `score_ref` | Pontuação LCS calculada pela versão sequencial |
| `media_seq_total_s` | Tempo médio sequencial de referência (em segundos) |
| `media_par_s` | Tempo médio gasto estritamente no trecho paralelo |
| `desvio_par_s` | Desvio padrão do tempo paralelo |
| `media_total_s` | Tempo médio total da execução |
| `desvio_total_s` | Desvio padrão do tempo total |
| `speedup` | Speedup obtido ($T_{seq\_total} / T_{total}$) |
| `eficiencia` | Eficiência paralela ($Speedup / (Processos \times Threads)$) |

#### 2. `detalhado.csv` e `detalhado_geral.csv`
Contém uma linha por repetição individual, permitindo analisar estabilidade térmica e variância do sistema:
* `caso`: Identificador do caso executado.
* `modo`: `--full-matrix` ou `--mem-opt`.
* `tipo_exec`: `sequencial`, `openmp`, `mpi` ou `hibrido`.
* `processos`, `threads`: Configuração de concorrência.
* `block_size`: Tamanho de bloco OpenMP configurado.
* `repeticao`: Número ordinal da repetição executada.
* `timestamp`: Data e hora exata da repetição.
* `tempo_seq_s`, `tempo_par_s`, `tempo_total_s`: Tempos medidos via temporizadores de alta precisão.
* `score`: Pontuação LCS calculada nesta repetição.
* `temp_start`, `temp_end`: Temperatura dos sensores da CPU no início e fim da execução (em °C).
* `freq_start_mhz`, `freq_end_mhz`: Frequência de operação dos núcleos (em MHz).
* `load_start`: Carga média do sistema (1-min load average) no instante do disparo.
* `mem_start_mb`: Memória RAM livre disponível antes da alocação.
* `returncode`: Código de saída do processo (0 = sucesso).

#### 3. `block_size.csv` e `block_size_geral.csv`
Resultados da análise de sensibilidade ao tamanho do bloco de tarefas OpenMP:
* `caso`, `modo`: Identificação da matriz testada.
* `threads`: Número de threads aplicadas (`4`, `8`, `16`).
* `block_size`: Candidato testado (`64`, `128`, `256`, `512`).
* `tempo_medio_s`, `desvio_s`: Tempo médio total e desvio padrão.
* `speedup`: Aceleração alcançada, evidenciando a diminuição de overhead de sincronização de tarefas à medida que o bloco se aproxima de 512.
* `eficiencia`: Eficiência correspondente.

#### 4. `ambiente_info.csv`
Metadados estáticos do ambiente de execução coletados na raiz de cada pasta:
* `propriedade`: Nome do parâmetro coletado (`hostname`, `cpu_model`, `cpu_cores_physical`, `cpu_threads_logical`, `total_ram_gb`, `os_distro`, `kernel`, `gcc_version`, `openmpi_version`, etc.).
* `valor`: Valor correspondente detectado na máquina.
