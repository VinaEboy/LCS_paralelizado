#ifndef MACROS_H
#define MACROS_H

//tipo menor para economizar memoria
typedef unsigned short mtype; 

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

#define BLOCK_SIZE 64

//flag DEBUG ativada
#define DEBUG 1

//flag de debug
#ifdef DEBUG
#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt, ##__VA_ARGS__)
#else
#define DEBUG_PRINT(fmt, ...) do {} while (0)
#endif


#endif
