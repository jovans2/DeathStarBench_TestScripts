#include <iostream>
#include <iterator>
#include <random>
#include <thread>

using namespace std;

void foo(int Z)
{
  for (int i = 0; i < Z; i++)
  {
    std::cout << "Thread using function pointer as callable\n";
  }
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