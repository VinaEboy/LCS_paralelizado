#ifndef MACROS_H
#define MACROS_H

//tipo menor para economizar memoria
typedef unsigned short mtype; 

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

#define BLOCK_SIZE 64

#define NUM_THREADS 4

//flag DEBUG ativada
#define DEBUG 1
#define DEBUGMATRIX 1 //era para imprimir a matriz

//flag de debug
#ifdef DEBUG
#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt, ##__VA_ARGS__)
#else
#define DEBUG_PRINT(fmt, ...) do {} while (0)
#endif

#endif
