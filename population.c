// Calculate the number of years required for the population to grow from the start size to the end size

#include <cs50.h>
#include <stdio.h>

int get_start_size(string prompt);
int get_end_size(string prompt, int start);
int get_years(int start, int end);

int main(void)
{
    int start = get_start_size("Start size: ");
    int end = get_end_size("End size: ", start);
    int years = get_years(start, end);

    printf("Years: %i\n", years);
}

// Prompt user for a starting population size greater than or equal to 9
int get_start_size(string prompt)
{
    int start;
    do
    {
        start = get_int("%s", prompt);
    }
    while (start < 9);

    return start;
}

// Prompt user for an ending population size greater than or equal to the starting population size
int get_end_size(string prompt, int start)
{
    int end;
    do
    {
        end = get_int("%s", prompt);
    }
    while (end < start);

    return end;
}

// Calculate the number of years required for the population to reach at least the size of the end value
int get_years(int start, int end)
{
    int years = 0;
    while (start < end)
    {
        // Each year, n / 3 new (people/animals) are born, and n / 4 (people/animals) pass away.
        start = start + (start / 3) - (start / 4);
        years++;
    }

    return years;
}
