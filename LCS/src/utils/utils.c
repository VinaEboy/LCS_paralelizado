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
        if ((seq[i] != '\n') && (seq[i] != '\r') && (seq[i] != EOF))
            i++;
    }
    seq[i] = '\0';
    
    fclose(fseq);
    return seq;
}


// aloca memoria para score matriz e para os dados contiguos
mtype** allocateScoreMatrix(int sizeA, int sizeB) {
    //allocate memory for LCS score matrix
    mtype *dados_contiguos = (mtype *) calloc((size_t)(sizeB + 1) * (sizeA + 1), sizeof(mtype));
    mtype **scoreMatrix = (mtype **) malloc((size_t)(sizeB + 1) * sizeof(mtype *));

    // aponta cada linha o seu respectivo lugar no bloco contíguo
    for (int i = 0; i < (sizeB + 1); i++) {
        scoreMatrix[i] = &dados_contiguos[(size_t)i * (sizeA + 1)];
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

// Debug 
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
            printf("%5u   ", (unsigned)scoreMatrix[i][j]);
        }
        printf("\n");
    }
    printf("========================================\n");
}

// para sabermos o tempo
double get_time() {
    return omp_get_wtime();
}

// versao sequencial otimizada em memoria (2 linhas)
mtype lcs_seq_mem_opt(char *seqA, char *seqB, int sizeA, int sizeB) {
    mtype *prev_row = (mtype *) calloc((size_t)(sizeA + 1), sizeof(mtype));
    mtype *curr_row = (mtype *) calloc((size_t)(sizeA + 1), sizeof(mtype));

    for (int i = 1; i <= sizeB; i++) {
        for (int j = 1; j <= sizeA; j++) {
            if (seqA[j - 1] == seqB[i - 1]) {
                curr_row[j] = prev_row[j - 1] + 1;
            } else {
                curr_row[j] = max(prev_row[j], curr_row[j - 1]);
            }
        }
        // troca as linhas para a proxima iteracao
        mtype *temp = prev_row;
        prev_row = curr_row;
        curr_row = temp;
    }

    mtype score = prev_row[sizeA];
    free(prev_row);
    free(curr_row);
    return score;
}
