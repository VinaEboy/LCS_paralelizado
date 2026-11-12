#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils_omp.h"

// ./lcs_omp [caminho fileA.in] [caminho fileB.in] [threads]
int main(int argc, char **argv) {
    double t_seq_start, t_seq_end, t_seq_total = 0.0;
    double t_par_start, t_par_end, t_par_total = 0.0;
    double t_total_start, t_total_end;

    t_total_start = get_time();
    t_seq_start = get_time();

    char *seqA, *seqB;
    int sizeA, sizeB;

    if (argc > 2) {
        seqA = read_seq(argv[1]);
        seqB = read_seq(argv[2]);
    } else {
        seqA = read_seq("fileA.in");
        seqB = read_seq("fileB.in");
    }

    sizeA = strlen(seqA);
    sizeB = strlen(seqB);

    mtype **scoreMatrix = allocateScoreMatrix(sizeA, sizeB);
    initScoreMatrix(scoreMatrix, sizeA, sizeB);
    t_seq_end = get_time();
    t_seq_total += (t_seq_end - t_seq_start);

    int num_threads;
    if (argc > 3) 
        num_threads = atoi(argv[3]);
    else
        num_threads = NUM_THREADS;

    t_par_start = get_time();
    lcs_omp_process_region(scoreMatrix, seqA, seqB, 1, sizeB, sizeA, num_threads);
    t_par_end = get_time();
    t_par_total = (t_par_end - t_par_start);

    t_seq_start = get_time();
    mtype score = scoreMatrix[sizeB][sizeA];

    #ifdef DEBUGMATRIX
    printMatrix(seqA, seqB, scoreMatrix, sizeA, sizeB);
    #endif

    free(seqA);
    free(seqB);
    freeScoreMatrix(scoreMatrix, sizeB);
    t_seq_end = get_time();
    t_seq_total += (t_seq_end - t_seq_start);

    t_total_end = get_time();

    printf("Score: %d\n", score);
    printf("Threads: %d\n", num_threads);
    printf("Tempo sequencial: %f s\n", t_seq_total);
    printf("Tempo paralelo: %f s\n", t_par_total);
    printf("Tempo total: %f s\n", (t_total_end - t_total_start));

    return EXIT_SUCCESS;
}
