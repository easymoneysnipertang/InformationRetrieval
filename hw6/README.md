# 倒排索引求交和压缩算法的并行化

## Makefile使用

* 修改main.cpp中的宏定义，选择求交算法：
```
#define isParallelOut true
#define Intersection SVS
```

`isParallelOut`决定是否在query间使用openMP多线程并行  
`Intersection`决定使用选择的求交算法：`SVS`、`SVS_SSE`、`SVS_OMP`

* 运行：  
```
make run
```

使用`ExpIndex`数据集构建倒排索引，使用`ExpQuery`进行查询测试，控制台输出求交所以时间  

* 清理：
```
make clean
```

清除编译生成的可执行文件。
