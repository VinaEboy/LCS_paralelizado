#ifndef UTILS_MPI
#define UTILS_MPI

#include "macros.h"

void mpi_initScoreMatrix(int rank, int size, int sizeA, int sizeB, int *inicio_linha,
                         int *num_minhas_linhas, mtype ***localMatrix, mtype **dados_locais);
void lcs_mpi_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA, 
        int inicio_linha, int num_minhas_linhas, int rank, int size);
void lcs_hybrid_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA,
        int inicio_linha, int num_minhas_linhas, int rank, int size, int num_threads);

#endif