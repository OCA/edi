This module extends the functionality of 'Voxel stock picking' module
to match secondary units of measure instead of standard units of measure
during the stock picking sending process.

During the process of a stock picking sending to Voxel, for each picking
move line, the following flow is followed:

* If 'secondary unit of measure' is set, this will be the unit of
  measure to be sent.
* If 'secondary unit of measure' is not set, standard quantity
  and standard unit of measure will be send.
