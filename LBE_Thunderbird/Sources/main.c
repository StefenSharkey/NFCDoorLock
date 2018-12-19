// Example: Turn on every other led
#include <hidef.h>      /* common defines and macros */
#include <mc9s12dg256.h>     /* derivative information */
#pragma LINK_INFO DERIVATIVE "mc9s12dg256b"

#include "main_asm.h" /* interface to the assembly module */

void main(void) {
  /* put your own code here */
  PLL_init();        // set system clock frequency to 24 MHz 
  DDRB  = 0x0f;       // Port B lower nibble is output
  // turn on every other led 
  PORTB   = 0x05;
  for(;;) {} /* wait forever */
}
