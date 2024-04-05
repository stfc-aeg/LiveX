#include <iostream>

template<typename T>
class FifoBuffer 
{
public:
    FifoBuffer(size_t size) : maxSize(size), front(0), back(0), count(0)
    {
        buffer = new T*[maxSize];
    }

    ~FifoBuffer()
    {
        delete[] buffer;
    }

    bool enqueue(T* item)
    {
        if (count >= maxSize){ // Buffer is full
          return false;
        }
        buffer[back] = item;
        back = (back + 1) % maxSize;
        count++;
        return true;
    }

    T* dequeue()
    {
        if (count == 0){ // Buffer is empty
            return nullptr;
        }
        T* item = buffer[front];
        front = (front + 1) % maxSize;
        count--;
        return item;
    }

    bool isEmpty() const
    {
        return count == 0;
    }

    bool isFull() const
    {
        return count == maxSize;
    }

    size_t size() const
    {
        return count;
    }

private:
    T** buffer; // Pointer to array of pointers to T
    size_t maxSize;
    size_t front, back, count;
};

struct BufferObject
{
    float counter;
    float temperatureA;
    float temperatureB;
};
