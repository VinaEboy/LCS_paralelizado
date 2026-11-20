#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "macros.h"

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

char* read_seq(char *fname);
mtype** allocateScoreMatrix(int sizeA, int sizeB);
void freeScoreMatrix(mtype **scoreMatrix, int sizeB);
void initScoreMatrix(mtype **scoreMatrix, int sizeA, int sizeB);

//debug
void printMatrix(char *seqA, char *seqB, mtype **scoreMatrix, int sizeA, int sizeB);

double get_time();

// versao sequencial otimizada em memoria (2 linhas)
mtype lcs_seq_mem_opt(char *seqA, char *seqB, int sizeA, int sizeB);

#endif
