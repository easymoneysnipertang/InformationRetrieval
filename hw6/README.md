# 倒排索引求交和压缩算法的并行化

## compression
索引压缩算法通常从两个方向展开：  
- d-gap变换与前缀和操作构成的数据变换方法以及文件重排技术等。  
- 整数编码算法：例如位对齐编码：Elias编码、Golomb/rice编码等；字节对齐编码：varint-SU、varint-GB等；以及固定宽度编码：PForDelta、newPFD、OptPFD。

对于变换与重排，选择对d-gap变换的优化进行研究。对于编码算法，选择固定编码中压缩比最高，但是解码速度较其他固定编码最慢的OptPFD作为终点并行化研究对象。  

## intersection
使用按表求交SvS算法：先使用两个表进行求交，得到中间结果再和第三个表求交，依次类推直到求交结束。  

### SIMD
对SVS算法最内侧循环，两列表求交遍历元素时进行SIMD并行化操作：  
使用_mm_set1_epi32指令将一个DocID填充向量四个位置，再从待比较列表取出四个元素放入另一向量，使用128位比较指令_mm_cmpeq_epi32一次比较当前列表四个元素。  
对比较结果，使用_mm_movemask_epi8指令生成掩码，判断掩码是否为0即可判断是否有交集。

### OpenMP
使用OpenMP进行query间并行化，在主线程将大量查询请求平均分配给多个子线程，子线程直接调用对应的求交算法。

## Makefile使用

* 修改main.cpp中的宏定义，选择求交算法与压缩/解压缩算法：
```C
// intersection/main.cpp
#define isParallelOut true
#define Intersect SVS
// compress/main.cpp
#define UseDGap true
#define Decompresss dgapDecompress
```

`isParallelOut`决定是否在query间使用OpenMP多线程并行  
`Intersect`决定选择的求交算法：`SVS`、`SVS_SSE`、`SVS_OMP`  
`UseDGap`决定选择的压缩算法：`dgapCompress`、`pfdCompress`  
`Decompress`决定选择的解压缩算法：`dgapDecompress`、`pfdDecompress`、`dgapDecompressOMP`、`pfdDecompressOMP`

* 运行：  
```
make run
```

**intersection**：使用`ExpIndex`数据集构建倒排索引，使用`ExpQuery`进行查询测试，控制台输出求交所用时间  
**compression**：对`ExpIndex`数据集进行压缩，保存为`compressed.bin`，控制台输出读取文件与解压缩所用时间

* 清理：
```
make clean
```

清除编译生成的可执行文件
