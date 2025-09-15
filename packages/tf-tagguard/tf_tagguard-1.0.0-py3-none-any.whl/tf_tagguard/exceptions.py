class TagValidationError(Exception):
    """Raised when a resource fails tag validation."""
    pass

class DuplicateTagDeclarationError(Exception):
    """Raised when a tag is declared in both -r and -v."""
    pass
