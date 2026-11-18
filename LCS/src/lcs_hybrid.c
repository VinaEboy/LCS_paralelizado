#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>
#include "utils.h"
#include "utils_mpi.h"

// ./lcs_mpi [caminho fileA.in] [caminho fileB.in] [threads]
int main(int argc, char **argv) {
    int rank, size, provided;
    int sizeA = 0, sizeB = 0;
    char *seqA = NULL, *seqB = NULL;

    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size); //aqui preenche o size

    double t_total_start = get_time();

    // processo 0 le os arquivos passados por argumento ou o default
    if (rank == 0) {
        if (argc > 2) {
            seqA = read_seq(argv[1]);
            seqB = read_seq(argv[2]);
        } else {
            seqA = read_seq("fileA.in");
            seqB = read_seq("fileB.in");
        }
        sizeA = strlen(seqA);
        sizeB = strlen(seqB);

        //Garante que o MPI corte a maior dimensão
        if (sizeB < sizeA) {
            char *tempSeq = seqA;
            seqA = seqB;
            seqB = tempSeq;
            
            int tempSize = sizeA;
            sizeA = sizeB;
            sizeB = tempSize;
        }
    }

    // transmite os tamanhos das sequencias para todos os processos
    MPI_Bcast(&sizeA, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&sizeB, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // aloca espaco para as sequencias nos outros ranks
    if (rank != 0) {
        seqA = (char *) calloc((size_t)sizeA + 1, sizeof(char));
        seqB = (char *) calloc((size_t)sizeB + 1, sizeof(char));
    }

    // transmite as duas sequencias completas para todos
    MPI_Bcast(seqA, sizeA + 1, MPI_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(seqB, sizeB + 1, MPI_CHAR, 0, MPI_COMM_WORLD);

    int num_minhas_linhas, inicio_linha;
    mtype *dados_locais = NULL;
    mtype **localMatrix = NULL;

    mpi_initScoreMatrix(rank, size, sizeA, sizeB, &inicio_linha, &num_minhas_linhas, &localMatrix, &dados_locais);

    int num_threads = (argc > 3) ? atoi(argv[3]) : NUM_THREADS;

    MPI_Barrier(MPI_COMM_WORLD);
    double t_par_start = get_time();

    lcs_hybrid_process(localMatrix, seqA, seqB, sizeA, inicio_linha, num_minhas_linhas, 
        rank, size, num_threads);

    double t_par_end = get_time();
    double t_total_end = get_time();

    // o ultimo rank possui o resultado final
    mtype final_score = 0;
    if (rank == size - 1) final_score = localMatrix[num_minhas_linhas][sizeA];

    // envia o score final para o rank 0 para impressao padronizada
    if (size > 1) {
        if (rank == size - 1) {
            MPI_Send(&final_score, 1, MPI_UNSIGNED_SHORT, 0, 99, MPI_COMM_WORLD);
        } else if (rank == 0) {
            MPI_Recv(&final_score, 1, MPI_UNSIGNED_SHORT, size - 1, 99, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }

    if (rank == 0) {
        printf("Score: %d\n", final_score);
        printf("Processos: %d\n", size);
        printf("Threads: %d\n", num_threads);
        printf("Tempo paralelo: %f s\n", (t_par_end - t_par_start));
        printf("Tempo total: %f s\n", (t_total_end - t_total_start));
    }

    free(dados_locais);
    free(localMatrix);
    free(seqA);
    free(seqB);

    MPI_Finalize();
    return EXIT_SUCCESS;
}
