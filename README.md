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
O objetivo deste trabalho é implementar, analisar e otimizar o algoritmo da **Maior Subsequência Comum (Longest Common Subsequence — LCS)** utilizando programação paralela em memória compartilhada (**OpenMP**), memória distribuída (**MPI**) e uma abordagem híbrida (**MPI + OpenMP**).

### Arquitetura das Implementações:
1. **Sequencial (`lcs_seq`):**
   - **Matriz Completa (`--full-matrix`):** Aloca e preenche toda a matriz de programação dinâmica $\mathcal{O}(M \times N)$.
   - **Otimizado em Memória (`--mem-opt`):** Utiliza apenas 2 linhas ativas, reduzindo a complexidade de espaço para $\mathcal{O}(N)$.

2. **OpenMP (`lcs_omp`):**
   - **Decomposição 2D em Blocos (*Tiling*):** A matriz é particionada em blocos de tamanho fixo (`--block-size N`, padrão `512`). Cada bloco é computado sequencialmente linha por linha internamente, garantindo máxima localidade espacial de cache L1d e reduzindo drásticamente *cache misses*.
   - **Avanço em Frente de Onda (*Wavefront*):** O avanço diagonal é gerenciado dinamicamente via grafo de tarefas assíncronas do OpenMP com dependências de dados (`#pragma omp task depend(in: ...) depend(out: ...)`).
   - **Modo `--mem-opt`:** Armazena apenas as bordas ativas (superior e esquerda) de cada bloco, permitindo resolver matrizes gigantescas com espaço proporcional a $\mathcal{O}(N_{blocos})$.

3. **MPI (`lcs_mpi`):**
   - **Decomposição 1D em Faixas Horizontais:** As linhas de $seqB$ são particionadas uniformemente entre os $P$ processos MPI.
   - **Pipeline Assíncrono de Chunks:** A largura das colunas é dividida em blocos de colunas (`--chunk-size N`, padrão `1024`). Cada processo calcula seu bloco e despacha a última linha para o processo vizinho abaixo via `MPI_Isend` / `MPI_Recv`.
   - **Modo `--mem-opt`:** Cada processo aloca apenas 2 linhas locais de tamanho $chunk\_size$, reduzindo o footprint de memória por processo para níveis mínimos.

4. **Híbrido MPI + OpenMP (`lcs_hybrid`):**
   - Combina a decomposição distribuída 1D entre processos MPI com o paralelismo de tarefas 2D OpenMP dentro da faixa de cada processo.
   - Suporte completo tanto a matriz completa quanto ao modo `--mem-opt`.

5. **Suporte Dual-Type (16 bits vs 32 bits):**
   - Por padrão, matrizes e buffers são alocados com `uint16_t` (`mtype`, alvo `make u16`), economizando 50% de RAM e tráfego de cache.
   - Para entradas de grande porte com score superior a 65.535 (como Q5, Q6, Q7, Q8, R5, R6), o código suporta `uint32_t` via compilação com a flag `-DMTYPE_32` (alvo `make u32`), eliminando qualquer risco de *overflow* aritmético.

---

## Parâmetros de Ajuste: `BLOCK_SIZE` e `CHUNK_SIZE`

* **`BLOCK_SIZE` (OpenMP e Híbrido) — Decisão Empírica:**
  - O valor padrão é **`512`**.
  - **Justificativa:** Definido experimentalmente através de varredura prévia com os valores 64, 128, 256 e 512 (executados pelo `run_test.py`). Blocos pequenos (como 64 e 128) geram centenas de milhares de tarefas, sobrecarregando o runtime OpenMP com custo de agendamento e sincronização. O tamanho 512 minimiza esse overhead, além de manter o bloco de dados confortavelmente dentro das caches L1d/L2 da CPU.
* **`CHUNK_SIZE` (MPI e Híbrido) — Decisão Arbitrária:**
  - O valor padrão é **`1024`**.
  - **Justificativa:** Escolha arbitrária de projeto para dimensionar o pipeline de mensagens MPI. Um chunk de 1024 colunas (2 KB em `u16` ou 4 KB em `u32`) oferece um compromisso adequado entre latência de inicialização do pipeline e vazão de rede (evitando fragmentação excessiva de mensagens).

---

## Mapeamento e Famílias de Entradas

O experimento avalia matrizes sintéticas determinísticas geradas pelo script `LCS/scripts/generate_input.py`, divididas em três categorias de tamanho e com variações de proporção e padrões de caracteres:

### 1. Dimensões e Proporções
* **Matrizes Quadradas:**
  - **Pequenas (*small*):** `Q1` ($1.000^2$), `Q2` ($10.000^2$), `Q3` ($20.000^2$) e casos especiais (`enunciado` $10 \times 7$, `quebrado` $827 \times 827$).
  - **Médias/Grandes (*big*):** `Q4` ($40.000^2$), `Q5` ($80.000^2$).
  - **Gigantescas (*giga*):** `Q6` ($100.000^2$), `Q7` ($160.000^2$), `Q8` ($320.000^2$).
* **Matrizes Retangulares (Razões Diretas e Invertidas):**
  - **Diretas:** `R1` ($80k \times 40k$, razão 2:1), `R2` ($80k \times 20k$, razão 4:1), `R3` ($80k \times 10k$, razão 8:1), `R4` ($160k \times 80k$, 2:1), `R5` ($160k \times 40k$, 4:1), `R6` ($160k \times 20k$, 8:1).
  - **Invertidas:** `R1_inv` ($40k \times 80k$, 1:2), `R2_inv` ($20k \times 80k$, 1:4), `R3_inv` ($10k \times 80k$, 1:8), `R4_inv` ($80k \times 160k$, 1:2), `R5_inv` ($40k \times 160k$, 1:4), `R6_inv` ($20k \times 160k$, 1:8).
  - *Objetivo:* Avaliar o impacto da assimetria entre linhas e colunas no particionamento horizontal do MPI e no wavefront do OpenMP.

### 2. Padrões de Caracteres Sintéticos
Cada família de entrada é avaliada sob 5 padrões de composição de caracteres:
* `p1`: Sequências **idênticas** (pior caso para LCS, score máximo = $N$).
* `p2`: Sequências **totalmente distintas** sem caracteres em comum (score zero).
* `p3`: Sequências com alfabeto reduzido de **4 caracteres** (ex: DNA $\{A, C, G, T\}$).
* `p4`: Sequências com **prefixo e sufixo comuns** e miolo divergente.
* `random`: Sequências com distribuição aleatória uniforme de caracteres.

---

## Estrutura do Repositório

```text
.
├── Enunciado Trabalho1 OpenMP_MPI.pdf
├── Relatório_Paralela/       # Código-fonte LaTeX do relatório e imagens
│   ├── main.tex
│   ├── sections/             # Seções modulares do relatório
│   ├── images_src/           # Códigos-fonte TikZ das ilustrações
│   └── images/               # Figuras vetoriais recortadas (.pdf)
├── Relatório_Paralela.pdf    # Relatório final compilado (8 páginas)
├── README.md
└── LCS/
    ├── Makefile              # Regras de compilação (u16, u32, seq, omp, mpi, hybrid)
    ├── include/
    │   ├── macros.h          # Definições de tipos (mtype 16/32 bits), constantes e defaults
    │   ├── utils.h           # Leitura de sequências, alocação e operações básicas
    │   ├── utils_omp.h       # Declarações das rotinas OpenMP e mem-opt
    │   └── utils_mpi.h       # Declarações de inicialização e pipelines MPI e Híbrido
    ├── src/
    │   ├── lcs_seq.c         # Ponto de entrada sequencial
    │   ├── lcs_omp.c         # Ponto de entrada OpenMP
    │   ├── lcs_mpi.c         # Ponto de entrada MPI
    │   ├── lcs_hybrid.c      # Ponto de entrada Híbrido (MPI + OpenMP)
    │   └── utils/
    │       ├── utils.c       # Implementação básica e I/O
    │       ├── utils_omp.c   # Kernel de tarefas e mem-opt OpenMP
    │       └── utils_mpi.c   # Pipeline MPI e Híbrido
    ├── scripts/
    │   ├── generate_input.py   # Gerador de entradas determinísticas
    │   ├── utils_experiment.py # Helpers de compilação, telemetria e execução
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
* **Python:** Python 3.8+ para os scripts automatizados (`pandas` opcional para análise).

### Configuração com Conda no cluster/máquina `duo`:
Se a máquina não possuir OpenMPI instalado no sistema global, utilize o ambiente Conda:
```bash
export PATH=~/miniconda3/envs/lcs-mpi/bin:$PATH
export OMPI_CC=gcc
```

---

## Como Compilar Manualmente

Dentro do diretório `LCS`:

```bash
cd LCS

# compilar versão padrão de 16 bits (u16)
make u16

# compilar versão estendida de 32 bits para matrizes gigantes (u32)
make u32

# compilar alvos individuais
make seq
make omp
make mpi
make hybrid

# limpeza de binários
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
mpirun --mca btl ^tcp -np 4 ./lcs_mpi inputs/small/Q2/Q2_p1/fileA.in inputs/small/Q2/Q2_p1/fileB.in --mem-opt --chunk-size 1024
```

### 4. Híbrido MPI + OpenMP (`lcs_hybrid`)
```bash
mpirun [opcoes_mpi] -np <processos> ./lcs_hybrid <fileA.in> <fileB.in> [threads] [--mem-opt | --full-matrix] [--block-size N] [--chunk-size N]
```
Exemplo com 2 processos e 4 threads por processo:
```bash
mpirun --mca btl ^tcp -np 2 ./lcs_hybrid inputs/small/Q2/Q2_p1/fileA.in inputs/small/Q2/Q2_p1/fileB.in 4 --mem-opt --block-size 512 --chunk-size 1024
```

---

## Execução dos Scripts Automatizados e Recompilação Dinâmica

Os scripts em Python orquestram todo o ciclo de testes e cuidam automaticamente da integridade numérica dos tipos de dados:

### Mecanismo de Recompilação Automática (`u16` vs `u32`)
Durante a execução de `run_experiment.py` ou `run_test.py`, a função auxiliar em `scripts/utils_experiment.py` inspeciona o comprimento máximo das sequências de entrada ($M, N$).
* Se $\min(M, N) > 65.535$ (casos como Q5, Q6, Q7, Q8, R5 e R6 no pior caso), o script aciona automaticamente `make clean && make u32` antes dos disparos, gerando binários que utilizam `uint32_t`.
* Para os casos em que $\min(M, N) \le 65.535$, o script aciona automaticamente `make clean && make u16`, garantindo a economia de 50% de memória e cache.
* Essa alternância é transparente ao usuário e evita tanto o *overflow* numérico quanto desperdícios de banda de memória.

### 1. Script de Teste e Validação de `BLOCK_SIZE` (`run_test.py`)
Executa um teste de sanidade rápido cobrindo casos representativos (`Q2`, `Q4` e `Q5`), seguido da **Varredura de BLOCK_SIZE** (testando `64`, `128`, `256` e `512` em `Q4` e `Q5`).

```bash
cd LCS
python3 scripts/run_test.py
```

### 2. Script do Experimento Principal Oficial (`run_experiment.py`)
Bateria de testes completa contendo todas as entradas (`small`, `big`, `giga`), matrizes quadradas e retangulares diretas/invertidas sob os 5 padrões de caracteres, com **20 repetições por configuração**.

Como a bateria completa pode levar algumas horas, recomenda-se a execução em background com `nohup`:

```bash
cd LCS
nohup python3 scripts/run_experiment.py > experimento.log 2>&1 &
```

Para acompanhar o progresso em tempo real:
```bash
tail -f experimento.log
```

---

## Estrutura de Diretórios dos Resultados

Todos os dados gerados são salvos **exclusivamente em formato CSV**, organizados por família:

```text
LCS/resultados/
├── testes/
│   ├── ambiente_info.csv      # Metadados de CPU, SO, GCC e OpenMPI
│   ├── sumarizado_geral.csv   # Médias, speedups e eficiências de todos os testes
│   ├── detalhado_geral.csv    # Todas as repetições individuais com telemetria
│   ├── block_size_geral.csv   # Varredura consolidada de BLOCK_SIZE
│   ├── Q2/
│   ├── Q4/
│   └── Q5/
│
└── experimentos/
    ├── ambiente_info.csv      # Metadados da máquina servidora
    ├── sumarizado_geral.csv   # Resultados consolidados gerais de todas as entradas
    ├── detalhado_geral.csv    # Registro detalhado de cada repetição (temperatura, clock, load, tempo)
    ├── Q1/ ... Q8/            # Pastas individuais por família quadrada
    ├── R1/ ... R6/            # Pastas individuais por família retangular direta
    ├── R1_inv/ ... R6_inv/    # Pastas individuais por família retangular invertida
    └── enunciado/             # Casos de validação
```

---

## Explicação das Colunas dos Arquivos CSV

### 1. `sumarizado_geral.csv` e `sumarizado.csv`
| Coluna | Descrição |
| :--- | :--- |
| `caso` | Identificador do caso de teste (ex: `Q2/Q2_p1`, `Q7/Q7_random`) |
| `modo` | `--full-matrix` (matriz completa) ou `--mem-opt` (otimizado em memória) |
| `tipo_exec` | Tipo do paralelismo: `sequencial`, `openmp`, `mpi` ou `hibrido` |
| `processos` | Quantidade de processos MPI utilizados (1 para sequencial e OpenMP) |
| `threads` | Quantidade de threads OpenMP por processo (1 para sequencial e MPI puro) |
| `block_size` | Tamanho do bloco utilizado nas tarefas OpenMP (`512`) |
| `score_ref` | Pontuação LCS calculada pela versão sequencial de referência |
| `media_seq_total_s` | Tempo médio sequencial total de referência (em segundos) |
| `media_par_s` | Tempo médio gasto estritamente no trecho paralelo |
| `desvio_par_s` | Desvio padrão do tempo paralelo |
| `media_total_s` | Tempo médio total da execução |
| `desvio_total_s` | Desvio padrão do tempo total |
| `speedup` | Speedup obtido ($T_{seq\_total} / T_{total}$) |
| `eficiencia` | Eficiência paralela ($Speedup / (Processos \times Threads)$) |

### 2. `detalhado_geral.csv` e `detalhado.csv`
Contém uma linha por repetição individual, permitindo analisar estabilidade térmica e variância do sistema:
* `caso`, `modo`, `tipo_exec`, `processos`, `threads`, `block_size`.
* `repeticao`: Número ordinal da repetição executada (1 a 20).
* `timestamp`: Data e hora exata do término da repetição.
* `tempo_seq_s`, `tempo_par_s`, `tempo_total_s`: Tempos medidos via temporizadores de alta precisão (`omp_get_wtime` / `MPI_Wtime`).
* `score`: Pontuação LCS calculada nesta repetição (usada para validar corretude).
* `temp_start`, `temp_end`: Temperatura dos sensores da CPU no início e fim da execução (°C).
* `freq_start_mhz`, `freq_end_mhz`: Frequência de operação dos núcleos (MHz).
* `load_start`: Carga média do sistema (1-min load average) no instante do disparo.
* `mem_start_mb`: Memória RAM livre disponível antes da alocação.
* `returncode`: Código de retorno do processo (0 = sucesso).

### 3. `block_size_geral.csv`
Resultados da análise de sensibilidade ao tamanho do bloco de tarefas OpenMP:
* `caso`, `modo`, `threads`, `block_size` (`64`, `128`, `256`, `512`).
* `tempo_medio_s`, `desvio_s`, `speedup`, `eficiencia`.
