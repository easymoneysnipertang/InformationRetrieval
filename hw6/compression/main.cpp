#include "bitOp.h"
#include "dgap.h"
#include "pfd.h"
#include <windows.h>

using namespace std;

int main()
{
    //---------------------------------------读取---------------------------------------
    vector<vector<unsigned>> invertedLists;  // 读取的链表
    vector<vector<unsigned>> decompressed;  // 解压后的链表应该等于invertedLists

    // 计时
    long long head, tail, freq;
    QueryPerformanceFrequency((LARGE_INTEGER*)&freq);
    QueryPerformanceCounter((LARGE_INTEGER*)&head);  // Start Time

    getIndex(invertedLists);  // 读取倒排链表

    // 计时终止
    QueryPerformanceCounter((LARGE_INTEGER*)&tail);  // End Time
    cout << "Read(orignal) Time:" << (tail - head) * 1000.0 / freq << " ms" << endl;

    vector<unsigned> compressedRes;  // 压缩结果
    vector<unsigned> compressed;  // 读出来的压缩链表
    vector<unsigned> curList;  // 当前解压的链表

    //---------------------------------------压缩---------------------------------------------
    int idx = 0;
    for (int i = 0; i < invertedLists.size(); i++)  // 对每个链表进行压缩，存到compressedRes中
       dgapCompress(invertedLists[i], compressedRes, idx, idx);
    
    // 将压缩结果写入文件
    vectorToBin(compressedRes, "compress.bin");

    //---------------------------------------解压---------------------------------------------
    QueryPerformanceFrequency((LARGE_INTEGER*)&freq);
    QueryPerformanceCounter((LARGE_INTEGER*)&head);  // Start Time
    // 从第0个bit开始读数据，解压
    int curIdx = 0;
    binToVector("compress.bin", compressed);  // 读取到compressed中，compressed应等于compressedRes

    QueryPerformanceCounter((LARGE_INTEGER*)&tail);  // End Time
    cout << "Read Compressed File Time:" << (tail - head) * 1000.0 / freq << " ms" << endl;

    dgapDecompressAll(compressed, decompressed);

    QueryPerformanceCounter((LARGE_INTEGER*)&tail);  // End Time
    cout << "Decompresss Time:" << (tail - head) * 1000.0 / freq << " ms" << endl;
    return 0;
}