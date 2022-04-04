* /!\ IMPORTANT /!\ when working w/ multiple workers
  you MUST restart the instance every time you add or modify a route from the UI
  (eg: w/ the endpoint module) otherwise is not granted that the routing map
  is going to be up to date on all workers.
  @simahawk as already a POC to fix this.

* add api docs helpers
* allow multiple HTTP methods on the same endpoint
