#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils_omp.h"

// ./lcs_omp [caminho fileA.in] [caminho fileB.in] [threads] [--mem-opt | --full-matrix] [--debug-matrix]
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

    int num_threads = NUM_THREADS;
    if (argc > 3 && argv[3][0] != '-') {
        num_threads = atoi(argv[3]);
    }

    // leitura de flags opcionais
    int mem_opt = 0;
    int debug_matrix = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--mem-opt") == 0) {
            mem_opt = 1;
        } else if (strcmp(argv[i], "--debug-matrix") == 0) {
            debug_matrix = 1;
        } else if (strcmp(argv[i], "--full-matrix") == 0) {
            mem_opt = 0;
        }
    }

    // checagem de erro se mem_opt e debug_matrix forem passados juntos
    if (mem_opt && debug_matrix) {
        fprintf(stderr, "Erro: não é possível usar --debug-matrix com --mem-opt pois a matriz completa não é amarzenada\n");
        free(seqA);
        free(seqB);
        return EXIT_FAILURE;
    }

    mtype score = 0;

    if (mem_opt) {
        t_seq_end = get_time();
        t_seq_total += (t_seq_end - t_seq_start);

        t_par_start = get_time();
        score = lcs_omp_process_mem_opt(seqA, seqB, sizeB, sizeA, num_threads);
        t_par_end = get_time();
        t_par_total = (t_par_end - t_par_start);

        t_seq_start = get_time();
        free(seqA);
        free(seqB);
        t_seq_end = get_time();
        t_seq_total += (t_seq_end - t_seq_start);

    } 
    else 
    {
        mtype **scoreMatrix = allocateScoreMatrix(sizeA, sizeB);
        initScoreMatrix(scoreMatrix, sizeA, sizeB);
        t_seq_end = get_time();
        t_seq_total += (t_seq_end - t_seq_start);

        t_par_start = get_time();
        lcs_omp_process_region(scoreMatrix, seqA, seqB, 1, sizeB, sizeA, num_threads);
        t_par_end = get_time();
        t_par_total = (t_par_end - t_par_start);

        t_seq_start = get_time();
        score = scoreMatrix[sizeB][sizeA];

        if (debug_matrix) {
            printMatrix(seqA, seqB, scoreMatrix, sizeA, sizeB);
        }

        free(seqA);
        free(seqB);
        freeScoreMatrix(scoreMatrix, sizeB);
        t_seq_end = get_time();
        t_seq_total += (t_seq_end - t_seq_start);
    }

    t_total_end = get_time();

    printf("Score: %d\n", score);
    printf("Threads: %d\n", num_threads);
    printf("Tempo sequencial: %f s\n", t_seq_total);
    printf("Tempo paralelo: %f s\n", t_par_total);
    printf("Tempo total: %f s\n", (t_total_end - t_total_start));

    return EXIT_SUCCESS;
}
