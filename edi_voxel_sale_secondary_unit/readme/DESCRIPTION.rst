This module extends the functionality of 'Voxel sale order' module
to match secondary units of measure instead of standard units of measure
during sale order import process.

During the process of a sales order import from voxel, for each sales
order line, the following flow is followed:

* If there is a matching 'secondary unit of measure', this is set and
  the imported qty is set as 'secondary qty'. Based on these data, the
  standard 'unit of measure' and 'quantity' are computed.
* If there is no matching 'secondary unit of measure', standard quantity
  and the matching standard unit of measure are set.
