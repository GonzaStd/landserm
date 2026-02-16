from landserm.config.loader import DOMAIN_NAMES, loadSchemaClass
from landserm.config.schemas import delivery
DELIVERY_METHODS = delivery.DeliveryConfig.model_fields.keys()

def domains(ctx, args, incomplete):
    """Complete domain names"""
    return [domain for domain in DOMAIN_NAMES if domain.startswith(incomplete)]

def deliveryMethods(ctx, args, incomplete):
    """Complete delivery methods"""
    return [method for method in DELIVERY_METHODS if method.startswith(incomplete)]

""" 
def pathToDomains(ctx, incomplete):
    return [] # Right now there isn't any nested fields in domains config.

def pathToPolicies(ctx, incomplete):
    pass

def pathToDelivery(ctx, incomplete):
    pass


switchConfigType = {
    "domains": pathToDomains,
    "policies": pathToPolicies,
    "delivery": pathToDelivery
}
configFunc = switchConfigType.get(configType)
return configFunc(ctx, incomplete)
"""

def pathToAttribute(ctx, args, incomplete):
    """Complete path to attribute with dot notation, depending on the config type."""
    configType = ctx.invoked_subcommand
    domain = ctx.params.get("domain")

    schemaClass = loadSchemaClass(configType, domain)

    if '.' not in incomplete:
        fields = list(schemaClass.model_fields.keys())
        return [f for f in fields if f.startswith(incomplete)]
    
    parts = incomplete.split('.')

