export OMPI_CC ?= gcc

CC = gcc
MPICC ?= mpicc
CFLAGS = -Wall -Wextra -O3 -fopenmp -Iinclude $(CFLAGS_EXTRA)

SRC_DIR = src
UTILS_DIR = src/utils
INC_DIR = include

HEADERS = $(wildcard $(INC_DIR)/*.h)

SRCS_COMMON = $(UTILS_DIR)/utils.c
SRCS_SEQ = $(SRC_DIR)/lcs_seq.c $(SRCS_COMMON)
SRCS_OMP = $(SRC_DIR)/lcs_omp.c $(UTILS_DIR)/utils_omp.c $(SRCS_COMMON)
SRCS_MPI = $(SRC_DIR)/lcs_mpi.c $(UTILS_DIR)/utils_mpi.c $(UTILS_DIR)/utils_omp.c $(SRCS_COMMON)
SRCS_HYBRID = $(SRC_DIR)/lcs_hybrid.c $(UTILS_DIR)/utils_mpi.c $(UTILS_DIR)/utils_omp.c $(SRCS_COMMON)

TARGET_SEQ = lcs_seq
TARGET_OMP = lcs_omp
TARGET_MPI = lcs_mpi
TARGET_HYBRID = lcs_hybrid

.PHONY: all clean seq omp mpi hybrid u16 u32

all: seq omp mpi hybrid

u16:
	$(MAKE) clean
	$(MAKE) all CFLAGS_EXTRA=""

u32:
	$(MAKE) clean
	$(MAKE) all CFLAGS_EXTRA="-DMTYPE_32"

seq: $(TARGET_SEQ)
omp: $(TARGET_OMP)
mpi: $(TARGET_MPI)
hybrid: $(TARGET_HYBRID)

$(TARGET_SEQ): $(SRCS_SEQ) $(HEADERS)
	$(CC) $(CFLAGS) $(SRCS_SEQ) -o $(TARGET_SEQ)

$(TARGET_OMP): $(SRCS_OMP) $(HEADERS)
	$(CC) $(CFLAGS) $(SRCS_OMP) -o $(TARGET_OMP)

$(TARGET_MPI): $(SRCS_MPI) $(HEADERS)
	$(MPICC) $(CFLAGS) $(SRCS_MPI) -o $(TARGET_MPI)

$(TARGET_HYBRID): $(SRCS_HYBRID) $(HEADERS)
	$(MPICC) $(CFLAGS) $(SRCS_HYBRID) -o $(TARGET_HYBRID)

clean:
	rm -f $(TARGET_SEQ) $(TARGET_OMP) $(TARGET_MPI) $(TARGET_HYBRID)
