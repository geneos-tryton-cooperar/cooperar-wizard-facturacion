from trytond.pool import Pool
from .wizard_facturacion import CrearFacturacionStart, CrearFacturacion

def register():
    Pool.register(
        CrearFacturacionStart,
        module='cooperar-wizard-facturacion', type_='model')

    Pool.register(
        CrearFacturacion,
        module='cooperar-wizard-facturacion', type_='wizard')