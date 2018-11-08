#-*- coding: utf-8 -*-
from trytond.pool import Pool
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.transaction import Transaction
import datetime
import calendar
from decimal import Decimal

class CrearFacturacionStart(ModelView):
    'Crear Facturacion Start'
    __name__ = 'wizard_facturacion.crear_facturacion.start'
    
    mes = fields.Selection(
        [
            ('1', '01'),
            ('2', '02'),
            ('3', '03'),
            ('4', '04'),
            ('5', '05'),
            ('6', '06'),
            ('7', '07'),
            ('8', '08'),
            ('9', '09'),
            ('10', '10'),
            ('11', '11'),
            ('12', '12'),
        ],
        'Mes de Facturacion', required=True
    )
    anio = fields.Integer('Anio de Facturacion', required=True)
    fecha_emision_factura = fields.Date('Fecha emision factura', required=True)

class CrearFacturacion(Wizard):
    'Crear Facturacion'
    __name__ = 'wizard_facturacion.crear_facturacion'

    start = StateView('wizard_facturacion.crear_facturacion.start',
        'cooperar-wizard-facturacion.view_crear_facturacion_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Crear Facturas', 'crear', 'tryton-ok', default=True),
            ])

    crear = StateTransition()

    def transition_crear(self):
        self.crear_facturas()
        return 'end'


    def crear_facturas(self):
        #import pudb;pu.db
        Asociadas = Pool().get('party.party')
        filtro_asociadas = [
                ('asociada', '=', True), 
        ]
        asociadas = Asociadas.search(filtro_asociadas)
        for asociada in asociadas:
            self.crear_sale(asociada)
            self.crear_cuota(asociada)


    def crear_sale_lines_cuota_sostenimiento(self, asociada):
        ret = []
        monto_cuota = Decimal(asociada.monto_actual_cuota)

        Producto = Pool().get('product.product')
        productos = Producto.search([('name','=','Cuota Sostenimiento')])

        for producto in productos:
            ret.append(self.crear_sale_line(1, producto, monto_cuota))
        return ret  


    def crear_sale_line(self, amount, product, unit_price):
        """
        Creamos una linea de ventas de acuerdo a los parametros que recibimos.
        """

        SaleLine = Pool().get('sale.line')
        new_line = SaleLine(
                product=product,
                quantity=Decimal(amount),
                description=product.name + " - " + str(amount),
                unit=product.default_uom,
                )

        new_line.unit_price = unit_price
        return new_line


    
    def buscar_pos(self):
        Pos = Pool().get('account.pos')
        pos = Pos.search([
            ('pos_type','=','electronic'), 
            ('number','=', 3) 
        ])
        return pos[0]



    def crear_sale(self, asociada):
        #Esta funcion se llama una vez por asociada.
        #import pudb; pu.db

        monthrange = calendar.monthrange(self.start.anio, int(self.start.mes))
        fi_date = datetime.date(self.start.anio, int(self.start.mes), 1)
        ff_date = datetime.date(self.start.anio, int(self.start.mes), monthrange[1])

        Sale = Pool().get('sale.sale')
        party = asociada
        
        pos = self.buscar_pos()

        with Transaction().set_context({"customer": party}):
            #Creamos la venta a la que le vamos a asociar las lineas de venta
            descripcion = str('Cuota sostenimiento - ' + party.name.encode('utf-8'))
            sale = Sale(
                    party = party,
                    description = str(descripcion),
                    payment_term = 1,
                    pos = pos,
            )

            #Creamos las lineas para los distintos tipos de productos
            sale_lines = []

            sale_lines.extend(self.crear_sale_lines_cuota_sostenimiento(asociada))
           
            sale.lines = sale_lines
            sale.save()

            Tax = Pool().get('account.tax')
            for i in sale.lines:
                up = i.unit_price
                tax_ids = i.on_change_product().get("taxes")  # lista de ids
                i.unit_price = up
                tax_browse_records = Tax.browse(tax_ids) or []
                i.taxes = tuple(tax_browse_records)
                i.save()
            sale.save()


            #Avanzamos a presupuesto
            sale.invoice_address = sale.party.address_get(type='invoice')
            sale.shipment_address = sale.party.address_get(type='delivery')

            sale.quote([sale])

            #Avanzamos a confirmado
            sale.confirm([sale])

            #Avanzamos a procesado. En este estado se crea la factura
            #de la venta.
            sale.process([sale])

            #Luego de ejecutar el workflow de la venta, la guardamos.
            sale.save()

            #Seteamos las fechas de creacion, punto de venta y tipo de factura.
            if sale.invoices:
                sale.invoices[0].invoice_date = self.start.fecha_emision_factura
                sale.invoices[0].pyafipws_concept = 2
                sale.invoices[0].pyafipws_billing_start_date = fi_date
                sale.invoices[0].pyafipws_billing_end_date = ff_date
                sale.invoices[0].save()


    def crear_cuota(self, asociada):
        #Esta funcion se llama una vez por asociada.
        Cuota = Pool().get('asociadas.cuota')
        cuota = Cuota()
        cuota.asociada = asociada
        cuota.mes = self.start.mes
        cuota.anio = self.start.anio
        cuota.pagada = False
        cuota.monto = asociada.monto_actual_cuota 
        cuota.save()

