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



void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, int start_row, int end_row, int total_cols, int num_threads, int block_size) {
    int num_rows, num_blocks_i, num_blocks_j;
    
    // calcula quantos blocos existem eixo y (linhas) e x (colunas)
    num_rows = end_row - start_row + 1;
    num_blocks_i = (num_rows + block_size - 1) / block_size;
    num_blocks_j = (total_cols + block_size - 1) / block_size;

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
                start_i = start_row + ((bi - 1) * block_size);
                end_i   = start_i + block_size;
                if (end_i > end_row + 1) {
                    end_i = end_row + 1;
                }

                start_j = 1 + ((bj - 1) * block_size);
                end_j   = start_j + block_size;
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

void lcs_omp_process_chunk(mtype **scoreMatrix, char *seqA, char *seqB, int start_row, 
        int end_row, int start_col, int end_col, int num_threads, int block_size) {
    // calcula quantos blocos existem eixo y (linhas) e x (colunas)
    int num_rows, num_cols, num_blocks_i, num_blocks_j;
    
    num_rows = end_row - start_row + 1;
    num_cols = end_col - start_col + 1;
    num_blocks_i = (num_rows + block_size - 1) / block_size;
    num_blocks_j = (num_cols + block_size - 1) / block_size;

    // alocacao com padding
    int sync_cols = num_blocks_j + 1;
    char *sync_matrix = (char *) calloc((num_blocks_i + 1) * sync_cols, sizeof(char));

    #pragma omp parallel num_threads(num_threads)
    #pragma omp single
    {
        // começa com 1 por causa do padding
        for (int bi = 1; bi <= num_blocks_i; bi++) {
            for (int bj = 1; bj <= num_blocks_j; bj++) {
                int start_i, end_i, start_j, end_j;
                
                //limites do bloco
                start_i = start_row + ((bi - 1) * block_size);
                end_i   = start_i + block_size;
                if (end_i > end_row + 1)  end_i = end_row + 1;                

                start_j = start_col + ((bj - 1) * block_size);
                end_j   = start_j + block_size;
                if (end_j > end_col + 1) end_j = end_col + 1;

                //dependencias dos blocos adjacentes né, cima e do lado esquerdo
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

// versao com otimizacao de memoria guardando apenas bordas de blocos
mtype lcs_omp_process_mem_opt(char *seqA, char *seqB, int total_rows, int total_cols, int num_threads, int block_size) {
    int num_blocks_i, num_blocks_j;

    num_blocks_i = (total_rows + block_size - 1) / block_size;
    num_blocks_j = (total_cols + block_size - 1) / block_size;

    // aloca apenas as bordas horizontais e verticais dos blocos
    mtype *horiz_borders = (mtype *) calloc((size_t)(num_blocks_i + 1) * (total_cols + 1), sizeof(mtype));
    mtype *vert_borders = (mtype *) calloc((size_t)(num_blocks_j + 1) * (total_rows + 1), sizeof(mtype));

    int sync_cols = num_blocks_j + 1;
    char *sync_matrix = (char *) calloc((size_t)(num_blocks_i + 1) * sync_cols, sizeof(char));

    // aloca buffers locais para cada thread computar seu bloco
    int b_stride = block_size + 1;
    mtype **thread_buffers = (mtype **) malloc((size_t)num_threads * sizeof(mtype *));
    for (int t = 0; t < num_threads; t++) {
        thread_buffers[t] = (mtype *) malloc((size_t)b_stride * b_stride * sizeof(mtype));
    }

    #pragma omp parallel num_threads(num_threads)
    #pragma omp single
    {
        for (int bi = 1; bi <= num_blocks_i; bi++) {
            for (int bj = 1; bj <= num_blocks_j; bj++) {
                int start_i, end_i, start_j, end_j;

                start_i = 1 + ((bi - 1) * block_size);
                end_i   = start_i + block_size;
                if (end_i > total_rows + 1) {
                    end_i = total_rows + 1;
                }

                start_j = 1 + ((bj - 1) * block_size);
                end_j   = start_j + block_size;
                if (end_j > total_cols + 1) {
                    end_j = total_cols + 1;
                }

                #pragma omp task \
                    depend(in: sync_matrix[(bi - 1) * sync_cols + bj]) \
                    depend(in: sync_matrix[bi * sync_cols + (bj - 1)]) \
                    depend(out: sync_matrix[bi * sync_cols + bj]) \
                    firstprivate(bi, bj, start_i, end_i, start_j, end_j)
                {
                    int bi_len = end_i - start_i;
                    int bj_len = end_j - start_j;
                    int tid = omp_get_thread_num();
                    mtype *local = thread_buffers[tid];

                    // preenche a borda superior do bloco a partir da borda inferior do bloco anterior
                    for (int j = 0; j <= bj_len; j++) {
                        local[0 * b_stride + j] = horiz_borders[(size_t)(bi - 1) * (total_cols + 1) + (start_j - 1 + j)];
                    }

                    // preenche a borda esquerda do bloco a partir da borda direita do bloco anterior
                    for (int i = 0; i <= bi_len; i++) {
                        local[i * b_stride + 0] = vert_borders[(size_t)(bj - 1) * (total_rows + 1) + (start_i - 1 + i)];
                    }

                    // calcula os elementos do bloco
                    for (int i = 1; i <= bi_len; i++) {
                        int gi = start_i + i - 1;
                        for (int j = 1; j <= bj_len; j++) {
                            int gj = start_j + j - 1;
                            if (seqA[gj - 1] == seqB[gi - 1]) {
                                local[i * b_stride + j] = local[(i - 1) * b_stride + (j - 1)] + 1;
                            } else {
                                local[i * b_stride + j] = max(local[(i - 1) * b_stride + j], local[i * b_stride + (j - 1)]);
                            }
                        }
                    }

                    // salva a borda inferior para os blocos seguintes
                    for (int j = 1; j <= bj_len; j++) {
                        horiz_borders[(size_t)bi * (total_cols + 1) + (start_j - 1 + j)] = local[bi_len * b_stride + j];
                    }

                    // salva a borda direita para os blocos seguintes
                    for (int i = 1; i <= bi_len; i++) {
                        vert_borders[(size_t)bj * (total_rows + 1) + (start_i - 1 + i)] = local[i * b_stride + bj_len];
                    }
                }
            }
        }
        #pragma omp taskwait
    }

    mtype score = horiz_borders[(size_t)num_blocks_i * (total_cols + 1) + total_cols];

    for (int t = 0; t < num_threads; t++) free(thread_buffers[t]);
    free(thread_buffers);
    free(horiz_borders);
    free(vert_borders);
    free(sync_matrix);
    return score;
}
