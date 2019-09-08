#include <cs50.h>
#include <stdio.h>


int main(void)
{
    string name = get_string("what is your name?\n");
    printf("hello, %s\n", name);
}
