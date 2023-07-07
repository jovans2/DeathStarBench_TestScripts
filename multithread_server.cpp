#include <iostream>
#include <iterator>
#include <random>
#include <thread>

using namespace std;

int foo(int Z)
{
  int suma = 0;
  for (int k = 0; k < 10; k++)
    for (int i = 0; i < 10000; i++)
        for (int j = 0; j < 10000; j++)
          {
            suma += (i+1) * (j+1) + k;
          }
  return suma;
}

int poissonArrival(double avgArr, int numReqs)
{
    // seed the RNG
    std::random_device rd; // uniformly-distributed integer random number generator
    std::mt19937 rng (rd ()); // mt19937: Pseudo-random number generation

    double averageArrival = 15;
    double lamda = 1 / averageArrival;
    std::exponential_distribution<double> exp (lamda);

    double sumArrivalTimes=0;
    double newArrivalTime;

    for (int i = 0; i < numReqs; ++i)
    {
    newArrivalTime=  exp.operator() (rng);// generates the next random number in the distribution
    sumArrivalTimes  = sumArrivalTimes + newArrivalTime;
    }
}

int main(){
    thread th1(foo, 3);
    th1.join();
    return 0;
}