from trytond.pool import Pool
from .wizard_facturacion import CrearFacturacionStart, CrearFacturacion, AutorizarFe

def register():
    Pool.register(
        CrearFacturacionStart,
        module='cooperar-wizard-facturacion', type_='model')

    Pool.register(
        CrearFacturacion,
        AutorizarFe, 
        module='cooperar-wizard-facturacion', type_='wizard')