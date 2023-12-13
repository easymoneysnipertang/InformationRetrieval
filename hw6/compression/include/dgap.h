#pragma once
#include "bitOp.h"
#include <omp.h>

#define NUM_THREADS 4

void dgapTransform(const vector<unsigned>& invertedIndex, vector<unsigned>& result)
{
	unsigned indexLen = invertedIndex.size();
	if (indexLen == 0)
		return;

	result.push_back(invertedIndex[0]);

	// d-gap前一项减去后一项,同时求最大间隔
	for (int i = 1; i < indexLen; i++)
	{
		unsigned delta = invertedIndex[i] - invertedIndex[i - 1];
		result.push_back(delta);
	}
}

// invertedIndex: 排好序的倒排索引
// result: 压缩后的索引
// idx：指向最后一个bit的指针,会自动调整
// usedBit：result中实际使用的bit数，以避免浪费
// return: 压缩后大小（bit）
long long dgapCompress(const vector<unsigned>& invertedIndex, vector<unsigned>& result, int& idx, int usedBit)
{
	unsigned indexLen = invertedIndex.size();
	if (indexLen == 0)
		return -1;

	vector<unsigned> deltaId;
	deltaId.push_back(invertedIndex[0]);
	unsigned maxDelta = invertedIndex[0];  // 最大间隔

	// d-gap前一项减去后一项,同时求最大间隔
	for (int i = 1; i < indexLen; i++)
	{
		unsigned delta = invertedIndex[i] - invertedIndex[i - 1];
		deltaId.push_back(delta);
		if (delta > maxDelta)
			maxDelta = delta;
	}

	unsigned maxBitNum = ceil(log2(maxDelta + 1));  // 整体最多使用maxBitNum位存储

	long long bitCnt = usedBit + 32 + 6 + maxBitNum * indexLen;  // 总共使用bit数 = 以使用的bit数+存该链表要使用的bit数
	result.resize((int)ceil(bitCnt / 32.0));

	writeBitData(result, idx, indexLen, 32);  // 写入元素个数
	writeBitData(result, idx + 32, maxBitNum, 6);  // 写入delta元素长度

	idx += 38;  // 从index+38位开始写压缩后的delta
	for (int i = 0; i < indexLen; i++)
	{
		writeBitData(result, idx, deltaId[i], maxBitNum);
		idx += maxBitNum;
	}
	return bitCnt;
}

// invertedIndex: dgap压缩好的倒排索引
// result：解缩后的索引
// idx：从第idx个bit开始解压
// return：解压后大小（bit)
vector<unsigned> dgapDecompress(const vector<unsigned>& compressedLists,  int& idx)
{
	vector<unsigned> result;
	//前32位是长度
	unsigned len = readBitData(compressedLists, idx, 32);
	result.reserve(len);// 不同与后面，resize
	//printf("%d\n", len);
	if (len == 0)
		return result;

	//6位是用的Bit数
	int bitNum = (int)readBitData(compressedLists, idx + 32, 6);
	idx += 38;

	unsigned delta = readBitData(compressedLists, idx, bitNum);
	idx += bitNum;
	result.push_back(delta);//第一个delta直接进去
	for (unsigned i = 1; i < len; i++)
	{
		delta = readBitData(compressedLists, idx, bitNum);
		idx += bitNum;
		result.push_back(result[i - 1] + delta);//后续的都要加上前一个放进去
	}
	return result;
}


vector<unsigned> dgapDecompressOMP(const vector<unsigned>& compressedLists, int& idx)
{
	//前32位是长度
	unsigned len = readBitData(compressedLists, idx, 32);
	vector<unsigned> result;
	result.resize(len);
	//printf("%d\n", len);
	if (len == 0)
		return result;
	//6位是用的Bit数
	int bitNum = (int)readBitData(compressedLists, idx + 32, 6);
	idx += 38;

	int seq_num = len / NUM_THREADS;// 每个线程处理元素数目
	if (seq_num == 0) {// 特殊情况，每段0个
		unsigned delta = readBitData(compressedLists, idx, bitNum);
		idx += bitNum;
		result[0] = delta;//第一个delta直接进去
		for (int i = 1; i < len; i++){
			delta = readBitData(compressedLists, idx, bitNum);
			idx += bitNum;
			result[i] = result[i - 1] + delta;//后续的都要加上前一个放进去
		}
		return result;
	}

#pragma omp parallel num_threads(NUM_THREADS)
	{
		int tid = omp_get_thread_num();// 当前线程tid
		int localIdx = idx + bitNum * tid * seq_num;
		unsigned delta = readBitData(compressedLists, localIdx, bitNum);// 找出该段第一个元素
		localIdx += bitNum;// 读走一个delta
		result[tid * seq_num] = delta;
		for (int j = 0; j < seq_num - 1; j++) {// 线程内进行前缀和
			delta = readBitData(compressedLists, localIdx, bitNum);
			localIdx += bitNum;
			result[tid * seq_num + j + 1] = delta + result[tid * seq_num + j];
		}
#pragma omp barrier
	}
#pragma omp single
	// 处理边界位置，方便后面并行使用
	for (int i = 2; i <= NUM_THREADS; i++)// 好像有隐式路障？
		result[i * seq_num - 1] += result[(i - 1) * seq_num - 1];

#pragma omp parallel num_threads(NUM_THREADS)
	{
		int tid = omp_get_thread_num();
		if (tid != 0) {// 0号线程不用做
			for (int j = 0; j < seq_num - 1; j++)// 其余线程每个元素加前面段的末尾元素
				result[tid * seq_num + j] += result[tid * seq_num - 1];
		}
	}
	idx += bitNum * NUM_THREADS * seq_num;// 调整idx指针
	// 串行处理剩余元素
#pragma single
	if (len % NUM_THREADS != 0) {
		for (int i = NUM_THREADS * seq_num; i < len; i++) {
			unsigned delta= readBitData(compressedLists, idx, bitNum);
			idx += bitNum;
			result[i] = result[i - 1]+delta;
		}
	}
	return result;
}


void dgapDecompressAll(const vector<unsigned>& compressedLists, vector<vector<unsigned>>& result)
{
	vector<unsigned> curList;
	int idx = 0;

	for (int i = 0; i < 2000; i++) //解压2000个链表,结果放在decompressed
	{
		curList = dgapDecompress(compressedLists, idx);

		//验证正确性用
		/*if (curList1.size() != curList2.size())
		{
			printf("wrong length\n");
			cout << curList1.size() << " " << curList2.size() << endl;
		}
		else {
			cout << curList1.size() << endl;
			for (int j = 0; j < curList1.size(); j++)
				if (curList1[j] != curList2[j])
					cout << "wrong" << endl;
		}*/
		
		result.push_back(curList);
		//curList.clear();
	}
}