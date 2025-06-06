The fetching/processing flow of the Ediversa sale order files is as follows:
- The scheduled action "EDI Ediversa: Import Sales" generates the EDI exchange records
  used to fetch the Ediversa sale order file.
- The scheduled action "Edi exchange check input sync" performs 2 actions:
	- It fetches the Ediversa sale order files of those EDI exchange records with
	  pending files.
	- It creates the sale order records from the EDI exchange records whose Ediversa
	  sale order files have been fetched. In this part of the process, new contacts
	  can be created in case they do not exist in the database yet.
