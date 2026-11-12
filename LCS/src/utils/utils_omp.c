#include "utils_omp.h"
#include <omp.h>

// cada worker calcula apenas o seu bloco de forma sequencial
static void compute_block(mtype **scoreMatrix, char *seqA, char *seqB, int start_i, int end_i, int start_j, int end_j) {
    for (int i = start_i; i < end_i; i++) {
        for (int j = start_j; j < end_j; j++) {
            if (seqA[j - 1] == seqB[i - 1]) {
                scoreMatrix[i][j] = scoreMatrix[i - 1][j - 1] + 1;
            } else {
                scoreMatrix[i][j] = max(scoreMatrix[i - 1][j], scoreMatrix[i][j - 1]);
            }
        }
    }
}



void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, int start_row, int end_row, int total_cols, int num_threads) {
    int num_rows, num_blocks_i, num_blocks_j;
    
    // calcula quantos blocos existem eixo y (linhas) e x (colunas)
    num_rows = end_row - start_row + 1;
    num_blocks_i = (num_rows + BLOCK_SIZE - 1) / BLOCK_SIZE;
    num_blocks_j = (total_cols + BLOCK_SIZE - 1) / BLOCK_SIZE;

    // alocacao com padding
    int sync_cols = num_blocks_j + 1;
    char *sync_matrix = (char *) calloc((num_blocks_i + 1) * sync_cols, sizeof(char)); // calloc aloca com inicializacao de 0s

    #pragma omp parallel num_threads(num_threads)
    #pragma omp single
    {
        // começa com 1 por causa do padding
        for (int bi = 1; bi <= num_blocks_i; bi++) {
            for (int bj = 1; bj <= num_blocks_j; bj++) {
                int start_i, end_i, start_j, end_j;
                
                //limites do bloco
                start_i = start_row + ((bi - 1) * BLOCK_SIZE);
                end_i   = start_i + BLOCK_SIZE;
                if (end_i > end_row + 1) {
                    end_i = end_row + 1;
                }

                start_j = 1 + ((bj - 1) * BLOCK_SIZE);
                end_j   = start_j + BLOCK_SIZE;
                if (end_j > total_cols + 1) {
                    end_j = total_cols + 1;
                }

                //dependencias
                #pragma omp task \
                    depend(in: sync_matrix[(bi - 1) * sync_cols + bj]) \
                    depend(in: sync_matrix[bi * sync_cols + (bj - 1)]) \
                    depend(out: sync_matrix[bi * sync_cols + bj]) \
                    firstprivate(start_i, end_i, start_j, end_j)
                {
                    compute_block(scoreMatrix, seqA, seqB, start_i, end_i, start_j, end_j);
                }
            }
        }
        #pragma omp taskwait
    } //taskwai aqui
    free(sync_matrix);
}
