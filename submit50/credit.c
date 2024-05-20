#include <cs50.h>
#include <stdio.h>

int get_num_digits(long cc);
bool validity(long card);
void cardtype(long card, int get_num_digits);
bool validamex(long card, int get_num_digits);
bool validmastercard(long card, int get_num_digits);
bool validvisa(long card, int get_num_digits);
bool sumvalid(long card);
int sumdigits(long card);
int multiply2_sum(long card);
int sum_remain_digits(long card);



int main(void)
{
    //Get card number
    long card;
    do
    {
        card = get_long("Number: ");
    }
    while (card < 0);
    int num_digits = get_num_digits(card);
    bool card_valid  = (sumvalid(card));
    if (card_valid)
    {
        cardtype(card, num_digits);
    }
    else
    {
        printf("%s", "INVALID\n");
    }

}


//Count Length
int get_num_digits(long cc)
{
    int i = 0;
    while (cc > 0)
    {
        cc = cc / 10;
        i++;
    }
    return i;
}

//Check Validity
bool validity(long card)

{
    if (get_num_digits(card) < 13 && get_num_digits(card) > 16)

    {
        return false;
    }

    return true;

}


//Function that does not return value, determine which card type.
void cardtype(long card, int get_num_digits)
{
    if (validamex(card, get_num_digits))

    {
        printf("%s", "AMEX\n");
    }

    else if (validmastercard(card, get_num_digits))
    {
        printf("%s", "MASTERCARD\n");
    }

    else if (validvisa(card, get_num_digits))
    {
        printf("%s", "VISA\n");
    }
    else
    {
        printf("INVALID\n");
    }
}

//AMEX
bool validamex(long card, int get_num_digits)
{
    int first_two = (card / 10000000000000);

    if ((get_num_digits == 15) && (first_two == 34 || first_two == 37))
    {
        return true;
    }
    else
    {
        return false;
    }
}

//MASTERCARD
bool validmastercard(long card, int get_num_digits)
{
    int first_two = (card / 100000000000000);

    if ((get_num_digits == 16) && (first_two > 50 && first_two < 56))
    {
        return true;
    }
    else
    {
        return false;
    }
}

//validvisa
bool validvisa(long card, int get_num_digits)
{
    if (get_num_digits == 13)
    {
        return ((int)(card / 1000000000000) == 4);
    }
    else if (get_num_digits == 16)
    {
        return ((int)(card / 1000000000000000) == 4);
    }
    else
    {
        return false;
    }
}


bool sumvalid(long card)
{
    //LUHN's ALGORITHM
    // Multiply every other digit by 2, starting with second-to-last digit, then add product's digit together
    int sum1 = sumdigits(card);

    //Add the sum to the sum of the digits that weren't multiplied by 2
    int sum2 = sum_remain_digits(card);

    //Total of sum1 + sum2
    int totalsum = sum1 + sum2;

    return ((totalsum % 10) == 0);
}

//Multiply every alternate/other digit by 2, starting with second-to-last digit.
int sumdigits(long card)
{
    bool isAlternateDigit = false;
    int sum = 0;
    while (card > 0)
    {
        if (isAlternateDigit)
        {
            sum = sum + multiply2_sum(card);
        }

        isAlternateDigit = !isAlternateDigit;
        card = card / 10;
    }
    return sum;
}


//Multiply every other digit by 2
int multiply2_sum(long card)
{
    int sumNum = 0;
    int current = 2 * (card % 10);
    while (current > 0)
    {

        sumNum = sumNum + (current % 10);
        current = current / 10;

    }
    return sumNum;

}

//Add the sum to the sum of the digits that weren't multiplied by 2.
int sum_remain_digits(long card)
{
    bool isAlternateDigit = true;
    int sum = 0;
    while (card > 0)
    {
        if (isAlternateDigit)
        {
            sum = sum + (card % 10);
        }

        isAlternateDigit = !isAlternateDigit;
        card = card / 10;
    }
    return sum;
}

