#include <cs50.h>
#include <stdio.h>

int main(void)
{
    int c= get_int("hight:");  
     \\get input
    while(c<1||c>8)        
          \\take othe input value if it exceed the limit
    {
     c= get_int("hight:");
     }
    for(int i=1;i<=c;i++)         
       \\to change the rows
    {
        for(int j=c-1;j>=i;j--)  
             \\to print whitespaces
           {
             printf(" ");
             }
        for(int k=1;k<=i;k++)    
               \\to print #
          {
            printf("#");
            }
 
    printf("\n"); 
      \\change the line
    }
}
