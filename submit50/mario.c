#include <cs50.h>
#include <stdio.h>

int main(void)
{
int n;
do
{
    n = get_int("Positive Number: ");
}
while (n < 1 || n > 8);

// For each row
for (int i = 0; i < n; i++)
{
    // For each column
    for (int j = 0; j < n; j++)
    {
        //print a dot/space
        if (i + j < n - 1)
         printf(" ");

        //Print a brick
        else
        printf("#");
    }

    //Move to next row
    printf("\n");
}
}