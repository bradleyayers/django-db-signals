

def enable():
    """
    Enable the signals by monkey-patching django.db
    """
    from . import hook
