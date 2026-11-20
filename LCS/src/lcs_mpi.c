#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>
#include "utils.h"
#include "utils_mpi.h"

// ./lcs_mpi [caminho fileA.in] [caminho fileB.in] 
int main(int argc, char **argv) {
    int rank, size;
    int sizeA = 0, sizeB = 0;
    char *seqA = NULL, *seqB = NULL;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    double t_total_start = get_time();

    int mem_opt = 0;
    int chunk_size = DEFAULT_CHUNK_SIZE;
    // leitura de parametros de otimizacao e chunk
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--mem-opt") == 0) {
            mem_opt = 1;
        } else if (strcmp(argv[i], "--full-matrix") == 0) {
            mem_opt = 0;
        } else if (strcmp(argv[i], "--chunk-size") == 0 && i + 1 < argc) {
            chunk_size = atoi(argv[i + 1]);
            i++;
        }
    }

    // processo 0 le os arquivos passados por argumento ou o default
    if (rank == 0) {
        if (argc > 2 && argv[1][0] != '-' && argv[2][0] != '-') {
            seqA = read_seq(argv[1]);
            seqB = read_seq(argv[2]);
        } else {
            seqA = read_seq("fileA.in");
            seqB = read_seq("fileB.in");
        }
        sizeA = strlen(seqA);
        sizeB = strlen(seqB);

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
    MPI_Bcast(&mem_opt, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&chunk_size, 1, MPI_INT, 0, MPI_COMM_WORLD);

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
    mtype final_score = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    double t_par_start = get_time();

    if (mem_opt) {
        // execucao paralela mpi com economia de memoria
        int comp_linhas = sizeB / size;
        int resto = sizeB % size;
        inicio_linha = 1 + (rank * comp_linhas) + (rank < resto ? rank : resto);
        int fim_linha = inicio_linha + comp_linhas + (rank < resto ? 1 : 0) - 1;
        num_minhas_linhas = fim_linha - inicio_linha + 1;

        mtype my_score = lcs_mpi_process_mem_opt(seqA, seqB, sizeA, 
                                                 inicio_linha, num_minhas_linhas, rank, size, chunk_size);
        if (rank == size - 1) final_score = my_score;
    } else {
        // execucao paralela mpi com matriz completa
        mpi_initScoreMatrix(rank, size, sizeA, sizeB, &inicio_linha, &num_minhas_linhas, &localMatrix, &dados_locais);

        lcs_mpi_process(localMatrix, seqA, seqB, sizeA, inicio_linha, num_minhas_linhas, rank, size, chunk_size);

        // o ultimo rank possui o resultado final na ultima posicao da sua ultima linha
        if (rank == size - 1) {
            final_score = localMatrix[num_minhas_linhas][sizeA];
        }
    }

    // envia o score final para o rank 0 para impressao padronizada
    if (size > 1) {
        if (rank == size - 1) {
            MPI_Send(&final_score, 1, MPI_MTYPE, 0, 99, MPI_COMM_WORLD);
        } else if (rank == 0) {
            MPI_Recv(&final_score, 1, MPI_MTYPE, size - 1, 99, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    }

    double t_par_end = get_time();
    double t_total_end = get_time();

    if (rank == 0) {
        printf("Score: %u\n", (unsigned int)final_score);
        printf("Processos: %d\n", size);
        printf("Tempo paralelo: %f s\n", (t_par_end - t_par_start));
        printf("Tempo total: %f s\n", (t_total_end - t_total_start));
    }

    if (!mem_opt) {
        free(dados_locais);
        free(localMatrix);
    }
    free(seqA);
    free(seqB);

    MPI_Finalize();
    return EXIT_SUCCESS;
}
