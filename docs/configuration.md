# InvoiceAgent Configuration Guide

This guide explains how to configure InvoiceAgent to include your company information, logo, and payment details on invoices.

## Company Information

Your company information appears at the top of each invoice, including your company name, address, phone number, and email address.

### Show Current Company Information

To see the current company information for the default template:

```
invoiceagent config company --show
```

For a specific template:

```
invoiceagent config company --template custom_template --show
```

### Update Company Information

To update your company information:

```
invoiceagent config company --name "Your Company" --address "123 Main St\nCity, State 12345" --phone "(123) 456-7890" --email "billing@yourcompany.com"
```

Note: Use `\n` to indicate line breaks in the address.

You can update individual fields:

```
invoiceagent config company --name "New Company Name"
invoiceagent config company --email "new-email@example.com"
```

### Company Logo

Your logo appears in the header of invoices. The recommended size is approximately 150 x 50 pixels.

To check if a logo is configured:

```
invoiceagent config logo
```

To add or update your logo:

```
invoiceagent config logo /path/to/your/logo.png
```

To remove your logo:

```
invoiceagent config logo --remove
```

## Payment Information

Payment information appears in the footer of invoices.

### Show Current Payment Information

To see the current payment information:

```
invoiceagent config payment --show
```

For a specific template:

```
invoiceagent config payment --template custom_template --show
```

### Update Payment Information

To update payment details:

```
invoiceagent config payment --details "Payment Details:\nBank Name: Example Bank\nAccount Name: Your Business\nAccount Number: 1234567890\nRouting Number: 987654321"
```

Note: Use `\n` to indicate line breaks in the payment details.

### Use a Payment Template

InvoiceAgent includes pre-defined templates for common payment methods:

```
invoiceagent config payment-template
```

This command will display templates for:
1. Bank transfers
2. PayPal
3. Cryptocurrency payments

Select a template and then customize it with your specific details using the `config payment` command.

## Invoice Templates

InvoiceAgent supports multiple invoice templates. The default template is used unless specified otherwise.

### List Available Templates

To list all available templates:

```
invoiceagent config templates
```

### Using Templates with Invoice Export

When exporting an invoice, you can specify which template to use:

```
invoiceagent invoice export INVOICE_ID --template template_name
```

## Client Information

Client information is stored in the database and managed through the client commands:

```
# Add a new client
invoiceagent client add

# List all clients
invoiceagent client list

# Update a client
invoiceagent client update CLIENT_ID --name "New Name" --email "new-email@example.com"
```

Client information will automatically be included in invoices generated for that client. 