#include <mpi.h>
#include "utils_mpi.h"
#include "utils_omp.h"

void mpi_initScoreMatrix(int rank, int size, int sizeA, int sizeB, int *inicio_linha,
                         int *num_minhas_linhas, mtype ***localMatrix, mtype **dados_locais) {
                             
    // Calcula divisão balanceada entre os processos
    int comp_linhas = sizeB / size;
    int resto = sizeB % size;

    // indices 1-based
    *inicio_linha = 1 + (rank * comp_linhas) + (rank < resto ? rank : resto);
    int fim_linha = *inicio_linha + comp_linhas + (rank < resto ? 1 : 0) - 1;
    
    *num_minhas_linhas = fim_linha - inicio_linha + 1;
    *dados_locais = (mtype *) calloc((size_t)((*num_minhas_linhas) + 1) * (sizeA + 1), sizeof(mtype));
    *localMatrix = (mtype **) malloc((size_t)((*num_minhas_linhas) + 1) * sizeof(mtype *));
    
    for (int i = 0; i <= *num_minhas_linhas; i++) {
        (*localMatrix)[i] = &((*dados_locais)[(size_t)i * (sizeA + 1)]);
    }
}

void lcs_mpi_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA, 
        int inicio_linha, int num_minhas_linhas, int rank, int size) {

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
}



// process do hibrido
void lcs_hybrid_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA,
        int inicio_linha, int num_minhas_linhas, int rank, int size, int num_threads) {

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += CHUNK_SIZE) {
        int fim_coluna = col + CHUNK_SIZE - 1;
        if (fim_coluna > sizeA) fim_coluna = sizeA;
        
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        lcs_omp_process_chunk(localMatrix, seqA, seqB, 1, num_minhas_linhas,
            col, fim_coluna, num_threads);

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&localMatrix[num_minhas_linhas][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
}