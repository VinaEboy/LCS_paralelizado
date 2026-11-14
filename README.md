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
O objetivo deste trabalho é analisar e otimizar o algoritmo da **Maior Subsequência Comum (Longest Common Subsequence — LCS)** utilizando técnicas de programação paralela e distribuída.

A implementação baseia-se em:
1. **Paralelismo com OpenMP:** Paralelização em grânulo fino com divisão da matriz em blocos (*tiling*) de tamanho $64 \times 64$, utilizando tarefas com grafo de dependências (`#pragma omp task depend`) para guiar a frente de onda (*wavefront*).
2. **Otimização de Memória (`--mem-opt`):** Redução do consumo de memória de $\mathcal{O}(N \times M)$ para armazenamento apenas das bordas ativas dos blocos, possibilitando processar matrizes colossais ($320.000 \times 320.000$) sem esgotamento de memória RAM.
3. **Paralelismo com MPI:** Decomposição de domínio por faixas de linhas entre múltiplos processos e comunicação em pipeline por blocos de colunas.

---

## Como Compilar

Dentro do diretório `LCS`:

```bash
cd LCS

# compilar versao sequencial e openmp
make seq omp

# compilar todas (incluindo mpi, se houver compilador mpicc disponivel)
make all
```

---

## Como Rodar um Exemplo

### 1. Versão Sequencial (`lcs_seq`)
```bash
./lcs_seq <arquivo_A> <arquivo_B> [--mem-opt | --full-matrix] [--debug-matrix]
```
Exemplo:
```bash
./lcs_seq inputs/small/Q1/Q1_p1/fileA.in inputs/small/Q1/Q1_p1/fileB.in --mem-opt
```

### 2. Versão OpenMP (`lcs_omp`)
```bash
./lcs_omp <arquivo_A> <arquivo_B> <threads> [--mem-opt | --full-matrix] [--debug-matrix]
```
Exemplo rodando com 8 threads:
```bash
./lcs_omp inputs/small/Q3/Q3_p1/fileA.in inputs/small/Q3/Q3_p1/fileB.in 8 --mem-opt
```

### 3. Versão MPI (`lcs_mpi`)
```bash
mpirun -np <num_processos> ./lcs_mpi <arquivo_A> <arquivo_B>
```
Exemplo rodando com 4 processos:
```bash
mpirun -np 4 ./lcs_mpi inputs/small/Q2/Q2_p1/fileA.in inputs/small/Q2/Q2_p1/fileB.in
```

---

## Como Executar os Experimentos

### 1. Gerar/Verificar Entradas de Teste
O script gera entradas determinísticas divididas em categorias (`small`, `big`, `giga`) com matrizes quadradas, retangulares e com 5 padrões de strings (`p1` a `p4` e `random`):
```bash
cd LCS
python3 scripts/generate_input.py
```

### 2. Executar a Bateria Completa com `nohup`
O orquestrador executa 20 repetições por configuração com coleta de telemetria de CPU (temperatura, frequência, carga e memória livre) e gera os CSVs em `LCS/resultados/`:
```bash
cd LCS
nohup python3 scripts/run_experiment.py > experimento.log 2>&1 &
```

Para monitorar o andamento em tempo real:
```bash
tail -f experimento.log
```

---

## TO DO
- [ ] - Fazer arquivo híbrido OpenMP + MPI
- [ ] - Atualizar `run_experiment`
- [ ] - Rodar experimento
- [ ] - Finalizar relatório
