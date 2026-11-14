#ifndef MACROS_H
#define MACROS_H

//tipo menor para economizar memoria
typedef unsigned short mtype; 

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

#define BLOCK_SIZE 64

// caso não seja passado o num de threads por parametro
#define NUM_THREADS 4

// para imprimir a matriz ao executar
#define DEBUGMATRIX 0


#endif
