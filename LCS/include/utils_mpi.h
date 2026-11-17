#ifndef UTILS_MPI
#define UTILS_MPI

void mpi_initScoreMatrix(mtype ** scoreMatrix, int sizeA, int sizeB, int size);
void lcs_mpi_process();
void lcs_hybrid_process();

#endif