
void mpi_initScoreMatrix(mtype ** scoreMatrix, int sizeA, int sizeB, int size) {
    // calcula divisao balanceada das linhas entre os processos
    int comp_linhas = sizeB / size;
    int resto = sizeB % size;

    // indices 1-based no espaco global de linhas de seqB
    int inicio_linha = 1 + (rank * comp_linhas) + (rank < resto ? rank : resto);
    int fim_linha = inicio_linha + comp_linhas + (rank < resto ? 1 : 0) - 1;
    int num_minhas_linhas = fim_linha - inicio_linha + 1;

    mtype *dados_locais = (mtype *) calloc((size_t)(num_minhas_linhas + 1) * (sizeA + 1), sizeof(mtype));
    mtype **localMatrix = (mtype **) malloc((size_t)(num_minhas_linhas + 1) * sizeof(mtype *));
    for (int i = 0; i <= num_minhas_linhas; i++) {
        localMatrix[i] = &dados_locais[(size_t)i * (sizeA + 1)];
    }

}


void lcs_mpi_process() {

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += CHUNK_SIZE) {
        int fim_coluna = col + CHUNK_SIZE - 1;
        if (fim_coluna > sizeA) {
            fim_coluna = sizeA;
        }
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // calcula as linhas locais para este bloco de colunas
        for (int i = 1; i <= num_minhas_linhas; i++) {
            int gi = inicio_linha + i - 1; // indice global em seqB
            for (int j = col; j <= fim_coluna; j++) {
                if (seqA[j - 1] == seqB[gi - 1]) {
                    localMatrix[i][j] = localMatrix[i - 1][j - 1] + 1;
                } else {
                    localMatrix[i][j] = max(localMatrix[i - 1][j], localMatrix[i][j - 1]);
                }
            }
        }

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&localMatrix[num_minhas_linhas][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
}



// process do hibrido
void lcs_hybrid_process() {

    // pipeline em blocos de colunas
    for (int col = 1; col <= sizeA; col += CHUNK_SIZE) {
        int fim_coluna = col + CHUNK_SIZE - 1;
        if (fim_coluna > sizeA) {
            fim_coluna = sizeA;
        }
        int tam_bloco = fim_coluna - col + 1;

        // se nao for o primeiro processo, recebe a linha de cima do processo anterior
        if (rank > 0) {
            MPI_Recv(&localMatrix[0][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // calcula as linhas locais para este bloco de colunas
        for (int i = 1; i <= num_minhas_linhas; i++) {
            int gi = inicio_linha + i - 1; // indice global em seqB
            for (int j = col; j <= fim_coluna; j++) {
                if (seqA[j - 1] == seqB[gi - 1]) {
                    localMatrix[i][j] = localMatrix[i - 1][j - 1] + 1;
                } else {
                    localMatrix[i][j] = max(localMatrix[i - 1][j], localMatrix[i][j - 1]);
                }
            }
        }

        // se nao for o ultimo processo, envia a sua ultima linha para o proximo processo
        if (rank < size - 1) {
            MPI_Send(&localMatrix[num_minhas_linhas][col], tam_bloco, 
                     MPI_UNSIGNED_SHORT, rank + 1, 0, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
}