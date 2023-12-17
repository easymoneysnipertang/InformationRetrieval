#include "bitOp.h"
#include "dgap.h"
#include "pfd.h"
#include <windows.h>

using namespace std;
// 压缩算法：dgapCompress、pfdCompress
#define UseDGap true
// 解压算法：dgapDecompress、pfdDecompress、dgapDecompressOMP、pfdDecompressOMP
#define Decompresss dgapDecompressOMP

void decompress(const vector<unsigned>& compressedLists, vector<vector<unsigned>>& result)
{
	vector<unsigned> curList;
	int idx = 0;

	for (int i = 0; i < 2000; i++)  // 解压2000个链表，结果放在decompressed
	{
		curList = Decompresss(compressedLists, idx);
		result.push_back(curList);
	}
}


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
    cout << "Read(orignal) Time: " << (tail - head) * 1000.0 / freq << " ms" << endl;

    vector<unsigned> compressedRes;  // 压缩结果
    vector<unsigned> compressed;  // 读出来的压缩链表
    vector<unsigned> curList;  // 当前解压的链表

    //---------------------------------------压缩---------------------------------------------
    int idx = 0;
    for (int i = 0; i < (int)invertedLists.size(); i++){  // 压缩，存到compressedRes中
        if(UseDGap)
            dgapCompress(invertedLists[i], compressedRes, idx, idx);
        else
            pfdCompress(invertedLists[i], compressedRes, idx);
    }
    
    // 将压缩结果写入文件
    vectorToBin(compressedRes, "compressed.bin");

    //---------------------------------------解压---------------------------------------------
    QueryPerformanceFrequency((LARGE_INTEGER*)&freq);
    QueryPerformanceCounter((LARGE_INTEGER*)&head);  // Start Time

    binToVector("compressed.bin", compressed);  // 读取到compressed中，compressed应等于compressedRes

    QueryPerformanceCounter((LARGE_INTEGER*)&tail);  // End Time
    cout << "Read Compressed File Time: " << (tail - head) * 1000.0 / freq << " ms" << endl;

    decompress(compressed, decompressed);

    QueryPerformanceCounter((LARGE_INTEGER*)&tail);  // End Time
    cout << "Decompresss Time: " << (tail - head) * 1000.0 / freq << " ms" << endl;
    return 0;
}