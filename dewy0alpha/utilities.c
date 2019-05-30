//helper functions for managing strings and so forth in compiler compiler
#ifndef UTILITIES_C
#define UTILITIES_C

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


//forward declare all functions
int clamp(int x, int min, int max);
size_t dewy_index(int index, int length);
char* substr(char* string, int start, int stop);
char* clone(char* string);
char* concatenate(char* left, char* right);
char* read_file(char* filename);


/**
    clamp an integer to a range
*/
int clamp(int x, int min, int max)
{
    if (x < min) x = min;
    else if (x > max) x = max;
    return x;
}

/**
    convert a Dewy style index to a size_t according to Dewy indexing rules for slicing
*/
size_t dewy_index(int index, int length)
{
    index = (index < 0) ? length + index : index;   //if negative, use end relative indexing 
    // printf("dewy index: %d\n", clamp(index, 0, length - 1));
    return (size_t) clamp(index, 0, length - 1);    //clamp the index to the range of the array length
}

/**
    return a substring according to dewy string slicing rules
*/
char* substr(char* string, int start, int stop)
{
    size_t length = strlen(string);
    size_t start_idx = dewy_index(start, length);
    size_t stop_idx = dewy_index(stop, length);

    //compute length of substring
    size_t substr_length = (start_idx < stop_idx) ? stop_idx - start_idx : 0;
    // printf("substring length: %d\n", substr_length);

    //perform copy
    char* substr = malloc((substr_length + 1) * sizeof(char));
    char* ptr = substr;
    for (size_t i = start_idx; i <= stop_idx; i++)
    {
        *ptr++ = string[i];
    }
    *ptr = 0; //add null terminator to end of string
    return substr;
}

/**
    get a copy of a string
*/
char* clone(char* string)
{
    char* copy = malloc(strlen(string) * sizeof(char));
    char* ptr = copy;
    while ((*ptr++ = *string++));
    return copy;
}

/**
    concatenate 2 strings together
*/
char* concatenate(char* left, char* right)
{
    char* combined = malloc((strlen(left) + strlen(right)) * sizeof(char));
    char* ptr = combined;
    while ((*ptr++ = *left++));
    ptr--;  //remove null terminator from left string
    while ((*ptr++ = *right++));
    return combined;
}

char* read_file(char* filename)
{
    //see: https://stackoverflow.com/questions/14002954/c-programming-how-to-read-the-whole-file-contents-into-a-buffer
    FILE *f = fopen(filename, "rb");
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);  /* same as rewind(f); */

    char *string = malloc(fsize + 1);
    fread(string, fsize, 1, f);
    fclose(f);

    string[fsize] = 0;

    return string;
}


#endif