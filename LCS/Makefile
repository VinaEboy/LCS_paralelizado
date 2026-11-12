CC = gcc
CFLAGS = -Wall -Wextra -O3 -fopenmp -Iinclude

SRC_DIR = src
UTILS_DIR = src/utils

SRCS_COMMON = $(UTILS_DIR)/utils.c
SRCS_SEQ = $(SRC_DIR)/lcs_seq.c $(SRCS_COMMON)
SRCS_OMP = $(SRC_DIR)/lcs_omp.c $(SRCS_COMMON)

TARGET_SEQ = lcs_seq
TARGET_OMP = lcs_omp

.PHONY: all clean seq omp

all: seq

seq: $(TARGET_SEQ)

omp: $(TARGET_OMP)

$(TARGET_SEQ): $(SRCS_SEQ)
	$(CC) $(CFLAGS) $(SRCS_SEQ) -o $(TARGET_SEQ)

$(TARGET_OMP): $(SRCS_OMP)
	$(CC) $(CFLAGS) $(SRCS_OMP) -o $(TARGET_OMP)

clean:
	rm -f $(TARGET_SEQ) $(TARGET_OMP)
