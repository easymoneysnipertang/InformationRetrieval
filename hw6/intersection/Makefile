# 指定编译器
CC = g++

# 指定编译选项
CFLAGS = -Wall -std=c++11 -fexec-charset=gbk -msse4.1 -fopenmp

# 目标文件
TARGET = main

# 默认目标
all: $(TARGET)

# 编译规则
$(TARGET): $(TARGET).cpp *.h
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).cpp

# 运行规则
run: $(TARGET)
	./$(TARGET)

# 清理规则
clean:
	rm -f $(TARGET)