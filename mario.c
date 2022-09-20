#include <cs50.h>
#include <stdio.h>

int main(void)
{
    int h, c, r;
    do{

        h = get_int("input the height : \n");
    }
    while( h < 1 || h > 8);

   for( r = 1; r <= h  ; r++){
     for(c = 1; c <= h-r ; c++)
         printf(" ");
      for(c = 1 ; c <= r ; c++)
           printf("#");
      for(c = 1; c <= 2; c++)
          printf(" ");
        for(c = 1; c <= r; c++)
             printf("#");
           printf("\n");}
}
