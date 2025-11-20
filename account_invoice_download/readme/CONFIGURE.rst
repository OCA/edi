The configuration takes place in the menu *Invoicing > Configuration > Import Vendor Bills > Download Bills*.

If you have several customer accounts with the same supplier, you need to create a *Download Bill Configuration* for each of them.

On each *Download Bill Configuration*, you will need to:

* select an Invoice Import Configuration,
* select a backend (the list of available backends will depend on the additionnal **account\_invoice\_download\_** modules that you have installed),
* a download method: *Manual* or *Automatic*.

If you select *Automatic* as *Download Method*, you will have to enter the credentials of your account (login and password usually). If you select *Manual* as *Download Method* and you don't want to enter the credentials of your account, they will be prompted on each manual download run in Odoo. You can also choose to enter your login and not your password; in this case, only your password will be prompted on each manual download run.

If you have selected *Automatic* as *Download Method* on some accounts, make sure that the scheduled action *Vendor Bills Auto-Download* is active and has a daily frequency.
