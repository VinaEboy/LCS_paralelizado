#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>
#include "utils.h"

// tamanho do bloco de colunas para o pipeline de comunicacao
#define CHUNK_SIZE 1024

// ./lcs_mpi [caminho fileA.in] [caminho fileB.in]
int main(int argc, char **argv) {
    int rank, size;
    int sizeA = 0, sizeB = 0;
    char *seqA = NULL, *seqB = NULL;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    double t_total_start = get_time();

    // processo 0 le os arquivos passados por argumento ou o default
    if (rank == 0) {
        if (argc > 2) {
            seqA = read_seq(argv[1]);
            seqB = read_seq(argv[2]);
        } else {
            seqA = read_seq("fileA.in");
            seqB = read_seq("fileB.in");
        }
        sizeA = strlen(seqA);
        sizeB = strlen(seqB);
    }

    // transmite os tamanhos das sequencias para todos os processos
    MPI_Bcast(&sizeA, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&sizeB, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // aloca espaco para as sequencias nos outros ranks
    if (rank != 0) {
        seqA = (char *) calloc((size_t)sizeA + 1, sizeof(char));
        seqB = (char *) calloc((size_t)sizeB + 1, sizeof(char));
    }

    // transmite as duas sequencias completas para todos
    MPI_Bcast(seqA, sizeA + 1, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(seqB, sizeB + 1, MPI_CHAR, 0, MPI_COMM_WORLD);

    // calcula divisao balanceada das linhas entre os processos
    int comp_linhas = sizeB / size;
    int resto = sizeB % size;

    // indices 1-based no espaco global de linhas de seqB
    int inicio_linha = 1 + (rank * comp_linhas) + (rank < resto ? rank : resto);
    int fim_linha = inicio_linha + comp_linhas + (rank < resto ? 1 : 0) - 1;
    int num_minhas_linhas = fim_linha - inicio_linha + 1;

    // cada rank aloca apenas a sua faixa local: (num_minhas_linhas + 1) x (sizeA + 1)
    // a linha local 0 representa a linha (inicio_linha - 1) global
    mtype *dados_locais = (mtype *) calloc((size_t)(num_minhas_linhas + 1) * (sizeA + 1), sizeof(mtype));
    mtype **localMatrix = (mtype **) malloc((size_t)(num_minhas_linhas + 1) * sizeof(mtype *));
    for (int i = 0; i <= num_minhas_linhas; i++) {
        localMatrix[i] = &dados_locais[(size_t)i * (sizeA + 1)];
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double t_par_start = get_time();

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += CHUNK_SIZE) {
        int fim_coluna = col + CHUNK_SIZE - 1;
        if (fim_coluna > sizeA) {
            fim_coluna = sizeA;
        }
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // calcula as linhas locais para este bloco de colunas
        for (int i = 1; i <= num_minhas_linhas; i++) {
            int gi = inicio_linha + i - 1; // indice global em seqB
            for (int j = col; j <= fim_coluna; j++) {
                if (seqA[j - 1] == seqB[gi - 1]) {
                    localMatrix[i][j] = localMatrix[i - 1][j - 1] + 1;
                } else {
                    localMatrix[i][j] = max(localMatrix[i - 1][j], localMatrix[i][j - 1]);
                }
            }
        }

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&localMatrix[num_minhas_linhas][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double t_par_end = get_time();
    double t_total_end = get_time();

    // o ultimo rank possui o resultado final na ultima posicao da sua ultima linha
    mtype final_score = 0;
    if (rank == size - 1) {
        final_score = localMatrix[num_minhas_linhas][sizeA];
    }

    // envia o score final para o rank 0 para impressao padronizada
    if (size > 1) {
        if (rank == size - 1) {
            MPI_Send(&final_score, 1, MPI_UNSIGNED_SHORT, 0, 99, MPI_COMM_WORLD);
        } else if (rank == 0) {
            MPI_Recv(&final_score, 1, MPI_UNSIGNED_SHORT, size - 1, 99, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }

    if (rank == 0) {
        printf("Score: %d\n", final_score);
        printf("Processos: %d\n", size);
        printf("Tempo paralelo: %f s\n", (t_par_end - t_par_start));
        printf("Tempo total: %f s\n", (t_total_end - t_total_start));
    }

    free(dados_locais);
    free(localMatrix);
    free(seqA);
    free(seqB);

    MPI_Finalize();
    return EXIT_SUCCESS;
}
