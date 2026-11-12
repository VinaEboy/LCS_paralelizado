#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"

int LCS(mtype ** scoreMatrix, int sizeA, int sizeB, char * seqA, char *seqB) {
	int i, j;
	for (i = 1; i < sizeB + 1; i++) {
		for (j = 1; j < sizeA + 1; j++) {
			if (seqA[j - 1] == seqB[i - 1]) {
				/* if elements in both sequences match,
				 the corresponding score will be the score from
				 previous elements + 1*/
				scoreMatrix[i][j] = scoreMatrix[i - 1][j - 1] + 1;
			} else {
				/* else, pick the maximum value (score) from left and upper elements*/
				scoreMatrix[i][j] =
						max(scoreMatrix[i-1][j], scoreMatrix[i][j-1]);
			}
		}
	}
	return scoreMatrix[sizeB][sizeA];
}

int main(int argc, char ** argv) {
	// sequence pointers for both sequences
	char *seqA, *seqB;

	// sizes of both sequences
	int sizeA, sizeB;

	//read both sequences
	if (argc > 2) {
		seqA = read_seq(argv[1]);
		seqB = read_seq(argv[2]);
	} else {
		seqA = read_seq("fileA.in");
		seqB = read_seq("fileB.in");
	}

	//find out sizes
	sizeA = strlen(seqA);
	sizeB = strlen(seqB);

	// allocate LCS score matrix
	mtype ** scoreMatrix = allocateScoreMatrix(sizeA, sizeB);

	//initialize LCS score matrix
	initScoreMatrix(scoreMatrix, sizeA, sizeB);

	//fill up the rest of the matrix and return final score (element locate at the last line and collumn)
	mtype score = LCS(scoreMatrix, sizeA, sizeB, seqA, seqB);

	/* if you wish to see the entire score matrix,
	 for debug purposes, define DEBUGMATRIX. */
	#ifdef DEBUGMATRIX
	printMatrix(seqA, seqB, scoreMatrix, sizeA, sizeB);
	#endif

	//print score
	printf("\nScore: %d\n", score);

	//free score matrix
	free(seqA);
	free(seqB);
	freeScoreMatrix(scoreMatrix, sizeB);

	return EXIT_SUCCESS;
}
