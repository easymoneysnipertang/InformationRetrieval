#pragma once
#include "bitOp.h"
#include "pfd.h"
#include <omp.h>

#define NUM_THREADS 4
#define USESIMD true

// invertedIndex: 排好序的倒排索引
// result: 压缩后的索引
// idx：指向最后一个bit的指针,会自动调整
// usedBit：result中实际使用的bit数，以避免浪费
long long dgapCompress(const vector<unsigned>& invertedIndex, vector<unsigned>& result, int& idx, int usedBit)
{
	unsigned indexLen = invertedIndex.size();
	if (indexLen == 0)
		return -1;

	vector<unsigned> deltaId;
	deltaId.push_back(invertedIndex[0]);
	unsigned maxDelta = invertedIndex[0];  // 最大间隔

	// d-gap前一项减去后一项,同时求最大间隔
	for (unsigned i = 1; i < indexLen; i++)
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
	for (unsigned i = 0; i < indexLen; i++)
	{
		writeBitData(result, idx, deltaId[i], maxBitNum);
		idx += maxBitNum;
	}
	return bitCnt;
}


// invertedIndex: dgap压缩好的倒排索引
// result：解缩后的索引
// idx：从第idx个bit开始解压
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


// 在原解压缩算法基础上添加SIMD和OpenMP
vector<unsigned> dgapDecompressOMP(const vector<unsigned>& compressedLists, int& idx)
{
	// 前32位是长度
	unsigned len = readBitData(compressedLists, idx, 32);
	vector<unsigned> result;
	result.resize(len);
	if (len == 0)
		return result;
	// 6位是用的Bit数
	int bitNum = (int)readBitData(compressedLists, idx + 32, 6);
	idx += 38;

	int seq_num = len / NUM_THREADS;  // 每个线程处理元素数目
	if (seq_num == 0) {  // 特殊情况，每段0个
		unsigned delta = readBitData(compressedLists, idx, bitNum);
		idx += bitNum;
		result[0] = delta;  //第一个delta直接进去
		for (unsigned i = 1; i < len; i++){
			delta = readBitData(compressedLists, idx, bitNum);
			idx += bitNum;
			result[i] = result[i - 1] + delta;  //后续的都要加上前一个放进去
		}
		return result;
	}

#pragma omp parallel num_threads(NUM_THREADS)
	{
		int tid = omp_get_thread_num();  // 当前线程tid
		int localIdx = idx + bitNum * tid * seq_num;
		unsigned delta = readBitData(compressedLists, localIdx, bitNum);  // 找出该段第一个元素
		localIdx += bitNum;  // 读走一个delta
		result[tid * seq_num] = delta;
		for (int j = 0; j < seq_num - 1; j++) {  // 线程内进行前缀和
			delta = readBitData(compressedLists, localIdx, bitNum);
			localIdx += bitNum;
			result[tid * seq_num + j + 1] = delta + result[tid * seq_num + j];
		}
#pragma omp barrier
	}
#pragma omp single
	// 处理边界位置，方便后面并行使用
	for (int i = 2; i <= NUM_THREADS; i++)  // 好像有隐式路障？
		result[i * seq_num - 1] += result[(i - 1) * seq_num - 1];

#pragma omp parallel num_threads(NUM_THREADS)
	{
		int tid = omp_get_thread_num();
		if (tid != 0) {  // 0号线程不用做
			int j = 0;
			// 使用simd做，一次加4个元素，注释以下部分即回到串行执行
			if(USESIMD){
				__m128i scalarValue = _mm_set1_epi32(result[tid * seq_num - 1]);
				for (; j < seq_num - 1 - 3; j += 4) {// 使用simd
					__m128i vector = _mm_loadu_si128((__m128i*)&result[tid * seq_num + j]);
					__m128i sum = _mm_add_epi32(scalarValue, vector);
					_mm_storeu_si128((__m128i*)&result[tid * seq_num + j], sum);
				}
			}
			for (; j < seq_num - 1; j++)  // 处理剩余元素
				result[tid * seq_num + j] += result[tid * seq_num - 1];
		}
	}
	idx += bitNum * NUM_THREADS * seq_num;  // 调整idx指针
	// 串行处理剩余元素
#pragma omp single
	if (len % NUM_THREADS != 0) {
		for (unsigned i = NUM_THREADS * seq_num; i < len; i++) {
			unsigned delta= readBitData(compressedLists, idx, bitNum);
			idx += bitNum;
			result[i] = result[i - 1]+delta;
		}
	}
	return result;
}
