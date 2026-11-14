#ifndef UTILS_OMP_H
#define UTILS_OMP_H

#include "utils.h"
#include "macros.h"

void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, 
                            int start_row, int end_row, int total_cols, int num_threads);

mtype lcs_omp_process_mem_opt(char *seqA, char *seqB, int total_rows, int total_cols, int num_threads);

#endif
