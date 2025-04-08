## Español
# Factura por tipo de venta

Este módulo asigna automáticamente una secuencia a las facturas según la plantilla del pedido de venta relacionado, reemplazando la automatización creada originalmente con Studio.

## Cómo probar

1. Crear un pedido de venta con plantilla "Alquiler", "Maquina", etc.
2. Confirmar el pedido.
3. Generar la factura (en borrador).
4. Verificar que el número de factura corresponde con la secuencia correspondiente.

## Dependencias

- account
- sale

## Inglés
# Invoice by Sale Type

This module assigns an invoice number automatically based on the sale order template used in the originating sale order.  
It replaces a Studio automation with standard Odoo code for licensing and maintainability purposes.

## Cómo probar

1. Create a Sale Order using one of the predefined templates (Rental, Machine, etc.)
2. Confirm the Sale Order
3. Create the invoice from it
4. Check that the invoice number has been auto-assigned according to the correct sequence

## Dependencias

- account
- sale