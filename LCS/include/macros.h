#ifndef MACROS_H
#define MACROS_H

#include <stdint.h>

#ifndef MTYPE_32
//tipo menor para economizar memoria
typedef uint16_t mtype;
#define MPI_MTYPE MPI_UNSIGNED_SHORT
#else
// tipo de 32 bits para pontuacoes maiores que 65535
typedef uint32_t mtype;
#define MPI_MTYPE MPI_UNSIGNED
#endif

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

// tem que descobrir um parametro bom
#define DEFAULT_BLOCK_SIZE 512
#define BLOCK_SIZE DEFAULT_BLOCK_SIZE

// tamanho default do bloco de colunas para mpi
#define DEFAULT_CHUNK_SIZE 1024
#define CHUNK_SIZE DEFAULT_CHUNK_SIZE

// caso não seja passado o num de threads por parametro
#define NUM_THREADS 4

// para imprimir a matriz ao executar
#define DEBUGMATRIX 0

#endif
