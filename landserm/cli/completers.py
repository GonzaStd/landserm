from landserm.config.loader import DOMAIN_NAMES, loadConfig
DELIVERY_METHODS = loadConfig("delivery").model_dump().keys()

def domains(ctx, args, incomplete):
    """Complete domain names"""
    return [domain for domain in DOMAIN_NAMES if domain.startswith(incomplete)]

def deliveryMethods(ctx, args, incomplete):
    """Complete delivery methods"""
    return [method for method in DELIVERY_METHODS if method.startswith(incomplete)]