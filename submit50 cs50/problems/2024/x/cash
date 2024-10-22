#include<cs50.h>
#include<stdio.h>

int calculate_quarters(int cents);
int main(void)
{
    //prompt the user for change owned (in cents)
    int cents;
    do
    {
        cents = get_int("Change owned: ");
    }
    while (cents < 0);
    //calculate how many quarters you should give the customer
    int quarters = calculate_quarters(cents);

    cents = cents - (quarters * 0.25);
}
int calculate_quarters(int cents)
{
      int quarters = 0;
    while (cents >= 25)
    {
        quarters++;
        cents= cents - 25;
    }
    return quarters;
}
