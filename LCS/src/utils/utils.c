#include "utils.h"
#include <omp.h>

// Lê a sequência do arquivo e retorna como string.
char* read_seq(char *fname) {
    FILE *fseq = NULL;
    long size = 0;
    char *seq = NULL;
    int i = 0;

    fseq = fopen(fname, "rt");
    if (fseq == NULL) {
        printf("Error reading file %s\n", fname);
        exit(1);
    }

    fseek(fseq, 0L, SEEK_END);
    size = ftell(fseq);
    rewind(fseq);

    seq = (char *) calloc(size + 1, sizeof(char));
    if (seq == NULL) {
        printf("Error allocating memory for sequence %s.\n", fname);
        exit(1);
    }

    while (!feof(fseq)) {
        seq[i] = fgetc(fseq);
        if ((seq[i] != '\n') && (seq[i] != EOF))
            i++;
    }
    seq[i] = '\0';
    
    fclose(fseq);
    return seq;
}


// aloca memoria para score matriz e para os dados contiguos
mtype** allocateScoreMatrix(int sizeA, int sizeB) {
    //Allocate memory for LCS score matrix
    mtype *dados_contiguos = (mtype *) calloc((sizeB + 1) * (sizeA + 1), sizeof(mtype));
    mtype **scoreMatrix = (mtype **) malloc((sizeB + 1) * sizeof(mtype *));

    // Aponta cada linha o seu respectivo lugar no bloco contíguo
    for (int i = 0; i < (sizeB + 1); i++) {
        scoreMatrix[i] = &dados_contiguos[i * (sizeA + 1)];
    }

    return scoreMatrix;
}

// libera memoria matriz
void freeScoreMatrix(mtype **scoreMatrix, int sizeB) {
    (void)sizeB;
    //agora está tudo de forma contígua é só liberar a posição 0
	free(scoreMatrix[0]);
    free(scoreMatrix);
}

// inicia 0 na linha 0 e coluna 0
void initScoreMatrix(mtype ** scoreMatrix, int sizeA, int sizeB) {
	int i, j;
	//Fill first line of LCS score matrix with zeroes
	for (j = 0; j < (sizeA + 1); j++)
		scoreMatrix[0][j] = 0;

	//Do the same for the first collumn
	for (i = 1; i < (sizeB + 1); i++)
		scoreMatrix[i][0] = 0;
}

// Debug com matriz pequena
void printMatrix(char *seqA, char *seqB, mtype **scoreMatrix, int sizeA, int sizeB) {
    printf("Score Matrix:\n");
    printf("========================================\n");
    printf("    ");
    printf("%5c   ", ' ');

    for (int j = 0; j < sizeA; j++)
        printf("%5c   ", seqA[j]);
    printf("\n");

    for (int i = 0; i < sizeB + 1; i++) {
        if (i == 0)
            printf("    ");
        else
            printf("%c   ", seqB[i - 1]);

        for (int j = 0; j < sizeA + 1; j++) {
            printf("%5d   ", scoreMatrix[i][j]);
        }
        printf("\n");
    }
    printf("========================================\n");
}

// para sabermos o tempo
double get_time() {
    return omp_get_wtime();
}
