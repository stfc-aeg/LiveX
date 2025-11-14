#ifndef FIFOBUFFER_H
#define FIFOBUFFER_H

#include <cstddef>

struct BufferObject
{
    float frame;
    // PID A attributes
    float temperature_upper;
    float output_upper;
    float kp_upper;
    float ki_upper;
    float kd_upper;
    float lastInput_upper;
    float outputSum_upper;
    float setpoint_upper;
    // PID B attributes
    float temperature_lower;
    float output_lower;
    float kp_lower;
    float ki_lower;
    float kd_lower;
    float lastInput_lower;
    float outputSum_lower;
    float setpoint_lower;
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