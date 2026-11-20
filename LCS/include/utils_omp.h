#ifndef UTILS_OMP_H
#define UTILS_OMP_H

#include <stdlib.h>
#include "utils.h"
#include "macros.h"

void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, 
                            int start_row, int end_row, int total_cols, int num_threads, int block_size);

void lcs_omp_process_chunk(mtype **scoreMatrix, char *seqA, char *seqB, int start_row, 
        int end_row, int start_col, int end_col, int num_threads, int block_size);

mtype lcs_omp_process_mem_opt(char *seqA, char *seqB, int total_rows, int total_cols, int num_threads, int block_size);

#endif
