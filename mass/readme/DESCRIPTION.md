When porting the **mass** module to Odoo 18, it was decided to move the merge the mass module into the module **donation_mass**. The experience shows that the mass module is never used without the donation module and that users are always given the same access rights on the mass module and the donation module. One of the major advantage of this merge is that it allows to use the **donation_type** field on products to configure the mass products.

Once you have successfully migrated to Odoo 18, you can remove this module (make sure that none of your specific modules has a depenency on it).
