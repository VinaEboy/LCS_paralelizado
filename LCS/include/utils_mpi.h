#ifndef UTILS_MPI
#define UTILS_MPI

#include "macros.h"

void mpi_initScoreMatrix(int rank, int size, int sizeA, int sizeB, int *inicio_linha,
                         int *num_minhas_linhas, mtype ***localMatrix, mtype **dados_locais);
void lcs_mpi_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA, 
        int inicio_linha, int num_minhas_linhas, int rank, int size, int chunk_size);
mtype lcs_mpi_process_mem_opt(char *seqA, char *seqB, int sizeA, 
        int inicio_linha, int num_minhas_linhas, int rank, int size, int chunk_size);
void lcs_hybrid_process(mtype **localMatrix, char *seqA, char *seqB, int sizeA,
        int inicio_linha, int num_minhas_linhas, int rank, int size, int num_threads, int chunk_size, int block_size);
mtype lcs_hybrid_process_mem_opt(char *seqA, char *seqB, int sizeA,
        int inicio_linha, int num_minhas_linhas, int rank, int size, int num_threads, int chunk_size, int block_size);

#endif