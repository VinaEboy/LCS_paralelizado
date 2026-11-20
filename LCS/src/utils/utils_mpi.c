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
    
    *num_minhas_linhas = fim_linha - (*inicio_linha) + 1;
    *dados_locais = (mtype *) calloc((size_t)((*num_minhas_linhas) + 1) * (sizeA + 1), sizeof(mtype));
    *localMatrix = (mtype **) malloc((size_t)((*num_minhas_linhas) + 1) * sizeof(mtype *));
    
    for (int i = 0; i <= *num_minhas_linhas; i++) {
        (*localMatrix)[i] = &((*dados_locais)[(size_t)i * (sizeA + 1)]);
    }
}

void lcs_mpi_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA, 
        int inicio_linha, int num_minhas_linhas, int rank, int size, int chunk_size) {

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += chunk_size) {
        int fim_coluna = col + chunk_size - 1;
        if (fim_coluna > sizeA) {
            fim_coluna = sizeA;
        }
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_MTYPE, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
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
                     MPI_MTYPE, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
}

mtype lcs_mpi_process_mem_opt(char *seqA, char *seqB, int sizeA, 
                              int inicio_linha, int num_minhas_linhas, int rank, int size, int chunk_size) {
    // aloca borda esquerda e buffers de linha para o pipeline
    mtype *left_border = (mtype *) calloc((size_t)(num_minhas_linhas + 1), sizeof(mtype));
    mtype *top_row     = (mtype *) calloc((size_t)(chunk_size + 1), sizeof(mtype));
    mtype *prev_row    = (mtype *) calloc((size_t)(chunk_size + 1), sizeof(mtype));
    mtype *curr_row    = (mtype *) calloc((size_t)(chunk_size + 1), sizeof(mtype));

    mtype final_score = 0;

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += chunk_size) {
        int fim_coluna = col + chunk_size - 1;
        if (fim_coluna > sizeA) fim_coluna = sizeA;
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&top_row[1], tam_bloco, MPI_MTYPE, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        } else {
            memset(&top_row[1], 0, tam_bloco * sizeof(mtype));
        }

        prev_row[0] = left_border[0];
        memcpy(&prev_row[1], &top_row[1], tam_bloco * sizeof(mtype));

        // calcula as linhas locais para este bloco de colunas
        for (int i = 1; i <= num_minhas_linhas; i++) {
            int gi = inicio_linha + i - 1; // indice global em seqB
            curr_row[0] = left_border[i];
            for (int j = 1; j <= tam_bloco; j++) {
                int gj = col + j - 1;
                if (seqA[gj - 1] == seqB[gi - 1]) {
                    curr_row[j] = prev_row[j - 1] + 1;
                } else {
                    curr_row[j] = max(prev_row[j], curr_row[j - 1]);
                }
            }
            left_border[i] = curr_row[tam_bloco];
            // alterna linhas para a proxima iteracao
            mtype *tmp = prev_row;
            prev_row = curr_row;
            curr_row = tmp;
        }

        left_border[0] = top_row[tam_bloco];

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&prev_row[1], tam_bloco, MPI_MTYPE, rank + 1, 0, MPI_COMM_WORLD);
        }

        // o ultimo processo na ultima coluna obtem o score final
        if (rank == size - 1 && fim_coluna == sizeA) {
            final_score = prev_row[tam_bloco];
        }
    }

    free(left_border);
    free(top_row);
    free(prev_row);
    free(curr_row);

    MPI_Barrier(MPI_COMM_WORLD);
    return final_score;
}

// process do hibrido
void lcs_hybrid_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA,
        int inicio_linha, int num_minhas_linhas, int rank, int size, int num_threads, int chunk_size, int block_size) {

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += chunk_size) {
        int fim_coluna = col + chunk_size - 1;
        if (fim_coluna > sizeA) fim_coluna = sizeA;
        
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_MTYPE, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        lcs_omp_process_chunk(localMatrix, seqA, seqB + (inicio_linha - 1), 1, num_minhas_linhas,
            col, fim_coluna, num_threads, block_size);

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&localMatrix[num_minhas_linhas][col], tam_bloco, 
                     MPI_MTYPE, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
}

mtype lcs_hybrid_process_mem_opt(char *seqA, char *seqB, int sizeA,
                                 int inicio_linha, int num_minhas_linhas, int rank, int size, 
                                 int num_threads, int chunk_size, int block_size) {
    // aloca borda esquerda e borda superior do chunk
    mtype *left_border = (mtype *) calloc((size_t)(num_minhas_linhas + 1), sizeof(mtype));
    mtype *top_row     = (mtype *) calloc((size_t)(chunk_size + 1), sizeof(mtype));

    // aloca submatriz local do chunk para openmp
    mtype **chunkMatrix = allocateScoreMatrix(chunk_size, num_minhas_linhas);
    mtype final_score = 0;

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += chunk_size) {
        int fim_coluna = col + chunk_size - 1;
        if (fim_coluna > sizeA) fim_coluna = sizeA;
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&top_row[1], tam_bloco, MPI_MTYPE, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        } else {
            memset(&top_row[1], 0, tam_bloco * sizeof(mtype));
        }

        // inicializa as bordas da matriz local do chunk
        chunkMatrix[0][0] = left_border[0];
        for (int j = 1; j <= tam_bloco; j++) chunkMatrix[0][j] = top_row[j];
        for (int i = 1; i <= num_minhas_linhas; i++) chunkMatrix[i][0] = left_border[i];

        // computa o chunk local em paralelo com tarefas openmp
        lcs_omp_process_chunk(chunkMatrix, seqA + (col - 1), seqB + (inicio_linha - 1),
                              1, num_minhas_linhas, 1, tam_bloco, num_threads, block_size);

        // atualiza a borda esquerda para o proximo chunk
        left_border[0] = top_row[tam_bloco];
        for (int i = 1; i <= num_minhas_linhas; i++) {
            left_border[i] = chunkMatrix[i][tam_bloco];
        }

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&chunkMatrix[num_minhas_linhas][1], tam_bloco, 
                     MPI_MTYPE, rank + 1, 0, MPI_COMM_WORLD);
        }

        // o ultimo processo na ultima coluna obtem o score final
        if (rank == size - 1 && fim_coluna == sizeA) {
            final_score = chunkMatrix[num_minhas_linhas][tam_bloco];
        }
    }

    freeScoreMatrix(chunkMatrix, num_minhas_linhas);
    free(left_border);
    free(top_row);

    MPI_Barrier(MPI_COMM_WORLD);
    return final_score;
}