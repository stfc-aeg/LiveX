#ifndef FIFOBUFFER_H
#define FIFOBUFFER_H

#include <cstddef>

struct BufferObject
{
    float counter;
    // PID A attributes
    float temperature_a;
    float output_a;
    float kp_a;
    float ki_a;
    float kd_a;
    float lastInput_a;
    float outputSum_a;
    float setpoint_a;
    // PID B attributes
    float temperature_b;
    float output_b;
    float kp_b;
    float ki_b;
    float kd_b;
    float lastInput_b;
    float outputSum_b;
    float setpoint_b;
};

template<typename T>
class FifoBuffer
{
    public:
        FifoBuffer(size_t size);
        ~FifoBuffer();
        bool enqueue(T* item);
        T* dequeue();
        bool isEmpty() const;
        bool isFull() const;
        size_t size() const;

    private:
        T** buffer;
        size_t maxSize;
        size_t front, back, count;
};

// Instantiate buffer of given size
template<typename T>
FifoBuffer<T>::FifoBuffer(size_t size) : maxSize(size), front(0), back(0), count(0)
{
    buffer = new T*[maxSize];
}

// Destructor for buffer
template<typename T>
FifoBuffer<T>::~FifoBuffer()
{
    delete[] buffer;
}

// Add an item to the buffer if there is room
template<typename T>
bool FifoBuffer<T>::enqueue(T* item)
{
    if (count >= maxSize) // buffer is full
    {
        return false;
    }
    // Adds to the back of the buffer and increases 'back', potentially circularly
    // However, the buffer is not used circularly is never utilised as it checks count vs maxSize
    buffer[back] = item;
    back = (back + 1) % maxSize;
    count++;
    return true;
}

// Remove an item from the buffer unless it is empty, returning nullptr instead
template<typename T>
T* FifoBuffer<T>::dequeue()
{
    if (count == 0) // buffer is empty
    {
        return nullptr;
    }
    T* item = buffer[front];
    front = (front + 1) % maxSize;
    count--;
    return item;
}

// Check if the buffer is empty
template<typename T>
bool FifoBuffer<T>::isEmpty() const
{
    return count == 0;
}

// Check if the buffer is full
template<typename T>
bool FifoBuffer<T>::isFull() const
{
    return count == maxSize;
}

// Get the current number of items in the buffer
template<typename T>
size_t FifoBuffer<T>::size() const
{
    return count;
}

#endif