First, you need to create an API Key. For that, login to your Scaleway account. On the top right, click on your organization and then click on *API Keys*.

Go to the *Applications* tab, create a new application called *odoo* (for example). Once created, on the new *odoo* application, click on the three horizontal dots and select *Overview*: add the application to the group *Billing Administrators*.

Then, go to the *API keys* tab, and create a new API key linked to the application *odoo*. Write down the secret key in a safe place. Your Scaleway API key is now ready!

In Odoo, go to the menu *Invoicing > Configuration > Import Vendor Bills > Download Bills* and create a new entry. Select *Scaleway* as *Backend* and set the Scaleway Secret Key.
