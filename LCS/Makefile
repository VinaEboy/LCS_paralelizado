CC = gcc
MPICC = mpicc
CFLAGS = -Wall -Wextra -O3 -fopenmp -Iinclude

SRC_DIR = src
UTILS_DIR = src/utils

SRCS_COMMON = $(UTILS_DIR)/utils.c
SRCS_SEQ = $(SRC_DIR)/lcs_seq.c $(SRCS_COMMON)
SRCS_OMP = $(SRC_DIR)/lcs_omp.c $(UTILS_DIR)/utils_omp.c $(SRCS_COMMON)
SRCS_MPI = $(SRC_DIR)/lcs_mpi.c $(SRCS_COMMON)

TARGET_SEQ = lcs_seq
TARGET_OMP = lcs_omp
TARGET_MPI = lcs_mpi

.PHONY: all clean seq omp mpi

all: seq omp

seq: $(TARGET_SEQ)

omp: $(TARGET_OMP)

mpi: $(TARGET_MPI)

$(TARGET_SEQ): $(SRCS_SEQ)
	$(CC) $(CFLAGS) $(SRCS_SEQ) -o $(TARGET_SEQ)

$(TARGET_OMP): $(SRCS_OMP)
	$(CC) $(CFLAGS) $(SRCS_OMP) -o $(TARGET_OMP)

$(TARGET_MPI): $(SRCS_MPI)
	$(MPICC) $(CFLAGS) $(SRCS_MPI) -o $(TARGET_MPI)

clean:
	rm -f $(TARGET_SEQ) $(TARGET_OMP) $(TARGET_MPI)
