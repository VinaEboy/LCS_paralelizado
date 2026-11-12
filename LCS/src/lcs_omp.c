#include "lcs_omp.h"
#include <omp.h>

// Cada worker calcula apenas o seu bloco
static void compute_block(mtype **scoreMatrix, char *seqA, char *seqB,
                          int start_i, int end_i, int start_j, int end_j) {
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

void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, 
                            int start_row, int end_row, int total_cols) {
    
    // Calcula quantos blocos existem no eixo Y (linhas) e X (colunas)
    int num_rows, num_blocks_i, num_blocks_j
    
    num_rows= end_row - start_row;
    num_blocks_i = (num_rows + BLOCK_SIZE - 1) / BLOCK_SIZE;
    num_blocks_j = (total_cols + BLOCK_SIZE - 1) / BLOCK_SIZE;

    // Alocação com Padding
    int sync_cols = num_blocks_j + 1;
    char *sync_matrix = calloc((num_blocks_i + 1) * sync_cols, sizeof(char));

    #pragma omp parallel
    #pragma omp single
    {
        // Começamos do 1 por causa do padding
        for (int bi = 1; bi < num_blocks_i; bi++) {
            for (int bj = 1; bj < num_blocks_j; bj++) {
                int start_i, end_i, start_j, end_j;
                // limites reais (em células) deste bloco específico
                start_i = start_row + ((bi-1) * BLOCK_SIZE);
                end_i   = start_i + BLOCK_SIZE;
                if (end_i > end_row) end_i = end_row;

                start_j = (bj == 1) ? 1 : ((bj-1) * BLOCK_SIZE);
                end_j   = start_j + BLOCK_SIZE;
                if (end_j > total_cols + 1) end_j = total_cols + 1;

                // grafo de dependencias
                #pragma omp task \
                    depend(in: sync_matrix[(bi - 1) * sync_cols + bj]) \
                    depend(in: sync_matrix[bi * sync_cols + (bj - 1)]) \
                    depend(out: sync_matrix[bi * sync_cols + bj])
                {
                    compute_block(scoreMatrix, seqA, seqB, start_i, end_i, start_j, end_j);
                }

            }
        }
    } // taskwait aqui
    free(sync_matrix);
}