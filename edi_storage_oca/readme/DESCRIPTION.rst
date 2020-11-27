Allow exchange files using storage backends from `OCA/storage`.

This module adds a storage backend relation on the EDI backend.
There you can configure the backend to be used (most often and SFTP)
and the paths where to read or put files.

Often the convention when exchanging files via SFTP
is to have one input forder (to receive files)
and an output folder (to send files).

Inside this folder you have this hierarchy::

    input/output folder
        |- pending
        |- done
        |- error

* `pending` folder contains files that have been just sent
* `done` folder contains files that have been processes successfully
* `error` folder contains files with errors and cannot be processed

The storage handlers take care of reading files and putting files
in/from the right place and update exchange records data accordingly.
