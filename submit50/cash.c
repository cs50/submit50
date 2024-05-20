#include <cs50.h>
#include <stdio.h>

int get_cents(void);
int calculate_quarters(int cents);
int calculate_dimes(int cents);
int calculate_nickels(int cents);
int calculate_pennies(int cents);

int main(void)
{
    // Ask how many cents the customer is owed
    int cents = get_cents();

    // Calculate the number of quarters to give the customer
    int quarters = calculate_quarters(cents);
    cents = cents - quarters * 25;

    // Calculate the number of dimes to give the customer
    int dimes = calculate_dimes(cents);
    cents = cents - dimes * 10;

    // Calculate the number of nickels to give the customer
    int nickels = calculate_nickels(cents);
    cents = cents - nickels * 5;

    // Calculate the number of pennies to give the customer
    int pennies = calculate_pennies(cents);
    cents = cents - pennies * 1;

    // Sum coins
    int coins = quarters + dimes + nickels + pennies;

    // Print total number of coins to give the customer
    printf("%i\n", coins);
}

int get_cents(void)
{
    int cents;
    //Loops for users to only type a POSITIVE integer
    do
    {
        cents = get_int("Cents Owed: ");
    }

    while (cents < 0);
    return cents;

}

int calculate_quarters(int cents)
{
    //To calculate the number quarters (25cent)
    int quarters = 0;

    //If remaining cent is more than 25cent, then -25 from total sum and +1 coin
    while (cents >= 25)
    {
        //Then total cent - quarter
        cents = cents - 25;
        //+1 quarter if cent > 25cent and repeat until it is = or < total amount
        quarters++;
    }
    //Return total number of quarters
    return quarters;
}

int calculate_dimes(int cents)
{
    //To calculate the number of dimes (10cent) after every possible <quarter> is deducted.
    int dimes = 0;
    //If remaining cent is more than 10cent, then -10 from total sum and +1 coin
    while (cents >= 10)
    {
        //Then total cent - dimes
        cents = cents - 10;
        //+1 dimes if cent > 10cent and repeat until it is = or < deducted amount
        dimes++;
    }
    return dimes;
}

int calculate_nickels(int cents)
{
    //To calculate the number of nickels (5cent) after every possible <quarter> and <dimes> is deducted.
    int nickels = 0;
    //If remaining cent is more than 5cent, then -5 from total sum and +1 coin
    while (cents >= 5)
    {
        //Then total cent - nickels
        cents = cents - 5;
        //+1 nickels if cent >5cent and repeat until it is = or < deducted amount
        nickels++;
    }
    return nickels;
}

int calculate_pennies(int cents)
{
    //To calculate the number of pennies(1cent) after every possible <quarter>, <dimes> & <nickels> is deducted.
    int pennies = 0;
    //If remaining cent is more than 1 cent, then -1 from total sum and +1 coin
    while (cents >= 1)
    {
        //Then total cent - pennies
        cents = cents - 1;
        //+1 pennies if cent >1cent and repeat until it is = or < deducted amount
        pennies++;
    }
    return pennies;
}
