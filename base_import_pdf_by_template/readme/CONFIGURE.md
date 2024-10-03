To configure a PDF document template for import, the first thing to do
is to have the document defined with a specific structure.

1.  Go to Settings \> Technical \> Base Import PDF Simple \> Templates
2.  Create a new template by entering a characteristic name and the
    model on which the record will be generated.

> Fields to consider completing on template:
>
> > - Main Model: model on which the record will be generated. Example:
> >   purchase.order
> > - Child field: One2many field that will create records from selected
> >   template. Example: Order Lines (purchase.order)
> > - Auto detect pattern: Define a characteristic pattern of the
> >   document so that it recognizes that it corresponds to the template
> >   we are creating. Need to use regular expression. Example:
> >   (?\<=ESA79935607)\[Ss\]\*
> > - Header Items: Complete this field if the template has a header
> >   table to extract information lines. Example:
> >   Reference,Quantity,Price
> > - Company: Set the company that will use the template. If it is
> >   empty, template will apply for all companies set on the
> >   environment.

1.  Add new lines.

> - Related model: When adding new line, the section where to locate the
>   data; "header" which, as its name indicates, refers to the header of
>   the document and "lines" refers to the structure of lines or table
>   of the document.
>
> - Field: Map the field to be completed. Example: product
>
> - Pattern: Optional field to complete. Define pattern of the document
>   so that it recognizes the place to get the field selected on PDF
>   template. Need to use regular expression. Example: (\[0-9\]{7})
>   \[0-7\]{1}
>
> - Value type:  
>   - Fixed: Select this value, if the field mapped will always have an
>     specific value and not extract the information from template. In
>     this case Pattern field must be empty.
>   - Variable: Select variable to get the information from template. In
>     this case, Pattern field must be completed.
>
> - For Value type "Variable" will appear extra fields to complete:
>
> - Search value: Indicates the field by which the value obtained in the
>   PDF will be searched on the system.
>
> - Default value: If the search result is empty for the search value
>   option, you can set default value to create a record and not getting
>   error message.
>
> - Log distint value?: This option is useful when getting prices in
>   order to compare prices inside system and prices obtained from PDF.
>   This will create lines with prices obtained from the system but
>   create log on chatter to see the differences obtained from PDF.

Check demo data to further information.
