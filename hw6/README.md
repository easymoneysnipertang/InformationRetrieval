# 倒排索引求交和压缩算法的并行化

## Makefile使用

* 修改main.cpp中的宏定义，选择求交算法与压缩/解压缩算法：
```C
// intersection/main.cpp
#define isParallelOut true
#define Intersect SVS
// compress/main.cpp
#define Compress pfdCompress
#define Decompresss pfdDecompress
```

`isParallelOut`决定是否在query间使用openMP多线程并行  
`Intersect`决定使用选择的求交算法：`SVS`、`SVS_SSE`、`SVS_OMP`  
`Compress`决定使用选择的压缩算法：`dgapCompress`、`pfdCompress`  
`Decompress`决定使用选择的解压缩算法：`dgapDecompress`、`pfdDecompress`

* 运行：  
```
make run
```

**intersection**：使用`ExpIndex`数据集构建倒排索引，使用`ExpQuery`进行查询测试，控制台输出求交所用时间  
**compression**：对`ExpIndex`数据集进行压缩，保存为`compressed.bin`，控制台输出文件读取与解压缩所用时间

* 清理：
```
make clean
```

清除编译生成的可执行文件。
