#include <stdio.h>
// CS50 Library for get_string
#include <cs50.h>

int main(void)
{
    // Asks user for their name
    string name = get_string("What is your name? ");
    // Prints hello, and the user's name
    printf("Hello, %s\n", name);
}