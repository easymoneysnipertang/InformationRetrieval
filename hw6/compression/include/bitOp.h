#pragma once
#include <iostream>
#include <fstream>
#include <bitset>
#include <algorithm>
#include <sstream>
#include <vector>
#include <math.h>

#define NUM_THREADS 4
using namespace std;

// 将n位数据写入到int型数组中
void writeBitData(vector<unsigned int>& array, unsigned int index, unsigned int data, int n)
{
    int shift = index % 32;
    int elementIndex = index / 32;
    int remainingBits = 32 - shift;
    unsigned mask = (long long)pow(2, n) - 1;
    if (remainingBits >= n) {
        // 跨越一个数组元素的情况
        array[elementIndex] &= ~(mask << shift);  // 清除对应位的数据
        array[elementIndex] |= (data & mask) << shift;  // 写入新数据
    }
    else {
        // 跨越两个数组元素的情况
        int bitsInFirstElement = remainingBits;
        int bitsInSecondElement = n - remainingBits;

        array[elementIndex] &= ~(mask << shift);  // 清除第一个元素中的数据
        array[elementIndex] |= (data & ((1 << bitsInFirstElement) - 1)) << shift;  // 写入第一个元素的数据

        array[elementIndex + 1] &= ~((1 << bitsInSecondElement) - 1);  // 清除第二个元素中的数据
        array[elementIndex + 1] |= (data >> bitsInFirstElement);  // 写入第二个元素的数据
    }
}

// 从unsigned int型数组中读取n位数据
unsigned int readBitData(const vector<unsigned int>& array, unsigned int index, int n) {
    unsigned int element_index = index / 32;
    unsigned int bit_position = index % 32;

    unsigned int mask = (unsigned)((long long)pow(2, n) - 1);// 注意不同cpu取整不一样
    unsigned int data = (array[element_index] >> bit_position) & mask;

    // 如果要读取的n位跨越了两个数组项
    if (bit_position > (unsigned)(32 - n)) {
        unsigned int next_element = array[element_index + 1];
        unsigned int remaining_bits = n - (32 - bit_position);
        data |= (next_element & ((1 << remaining_bits) - 1)) << (n - remaining_bits);
    }

    return data;
}

// 读取二进制索引文件
void getIndex(vector<vector<unsigned>>& invertedLists)
{
    fstream file;
    file.open("../ExpIndex", ios::binary | ios::in);
    if (!file.is_open()) {
        cout << "Wrong in opening file!";
        return;
    }
    unsigned int maxdocId = 0;
    double avgLen = 0;
    for (int i = 0; i < 2000; i++)  //  总共读取2000个倒排链表
    {
        vector<unsigned> t;  // 一个倒排链表
        int len;
        file.read((char*)&len, sizeof(len));
        avgLen += len;
        for (int j = 0; j < len; j++)
        {
            unsigned int docId;  // 文件id
            file.read((char*)&docId, sizeof(docId));
            t.push_back(docId);  // 加入至倒排表
            if (docId > maxdocId)
                maxdocId = docId;
        }
        sort(t.begin(), t.end());  // 对文档编号排序
        invertedLists.push_back(t);  // 加入一个倒排表
    }
    cout << maxdocId << endl;
    cout << avgLen / 2000 << endl;
    file.close();

    cout << "-----file loaded-----" << endl;
}

// 将索引写入二进制文件
void vectorToBin(const vector<unsigned int>& data, const string& filename)
{
    // 打开二进制文件用于写入
    ofstream file(filename, ios::binary);
    if (!file.is_open()) {
        cerr << "Failed to open the file: " << filename << endl;
        return;
    }

    // 将向量中的每个元素写入文件
    for (const unsigned int& element : data) {
        file.write(reinterpret_cast<const char*>(&element), sizeof(unsigned int));
    }

    // 关闭文件
    file.close();
}

// 从二进制文件中读取索引
void binToVector(const string& filename, vector<unsigned int>& data)
{

    // 打开二进制文件用于读取
    ifstream file(filename, ios::binary);
    if (!file.is_open()) {
        cerr << "Failed to open the file: " << filename << endl;
        return;
    }

    // 获取文件大小
    file.seekg(0, ios::end);
    streampos fileSize = file.tellg();
    file.seekg(0, ios::beg);

    // 计算向量大小
    size_t numElements = fileSize / sizeof(unsigned int);
    data.resize(numElements);

    // 从文件读取数据到向量
    file.read(reinterpret_cast<char*>(data.data()), fileSize);

    // 关闭文件
    file.close();
}