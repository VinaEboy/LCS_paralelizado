#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef max
#define max( a, b ) ( ((a) > (b)) ? (a) : (b) )
#endif

typedef unsigned short mtype;

char* read_seq(char *fname);
mtype** allocateScoreMatrix(int sizeA, int sizeB);
void freeScoreMatrix(mtype **scoreMatrix, int sizeB);
void initScoreMatrix(mtype **scoreMatrix, int sizeA, int sizeB);

//debug
void printMatrix(char *seqA, char *seqB, mtype **scoreMatrix, int sizeA, int sizeB);
double get_time();

#endif