from trytond.pool import Pool
from .wizard_facturacion import CrearFacturacionStart, CrearFacturacion
from .autorizar_fe import AutorizarFeStart, AutorizarFe

def register():
    Pool.register(
        CrearFacturacionStart,
        AutorizarFeStart,
        module='cooperar-wizard-facturacion', type_='model')

    Pool.register(
        CrearFacturacion,
        AutorizarFe, 
        module='cooperar-wizard-facturacion', type_='wizard')