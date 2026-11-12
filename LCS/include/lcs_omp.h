#ifndef LCS_OMP_H
#define LCS_OMP_H

#include "utils.h"

#define BLOCK_SIZE 64

/* 
 * Função que o MPI vai chamar para processar a sua faixa de linhas.
 * Ela internamente fatia a matriz em blocos e dispara as tasks.
 */
void lcs_omp_process_region(mtype **scoreMatrix, char *seqA, char *seqB, 
                            int start_row, int end_row, int total_cols);

#endif