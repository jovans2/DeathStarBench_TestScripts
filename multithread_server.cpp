#include <iostream>
#include <iterator>
#include <random>
#include <thread>
#include <chrono>

using namespace std;
using namespace std::chrono;

using std::chrono::duration_cast;
using std::chrono::milliseconds;
using std::chrono::system_clock;

int foo(int Z)
{
  auto start = high_resolution_clock::now();
  int suma = 0;
  for (int k = 0; k < 1; k++)
    for (int i = 0; i < 10000; i++)
        for (int j = 0; j < 10000; j++)
          {
            suma += (i+1) * (j+1) + k;
          }
  auto stop = high_resolution_clock::now();
  auto duration = duration_cast<milliseconds>(stop-start).count();
  std::cout << "Duration = " << duration << std::endl;
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