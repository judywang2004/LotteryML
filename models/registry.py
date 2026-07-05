MODELS = {}

def register(method_name, model):
    """
    Register one prediction model.
    """

    method_name = method_name.lower()

    if method_name in MODELS:
        raise ValueError(f"Duplicate model: {method_name}")

    MODELS[method_name] = model


def get_model(method_name):

    method_name = method_name.lower()

    if method_name not in MODELS:

        raise ValueError(
            f"Unknown prediction method: {method_name}"
        )

    return MODELS[method_name]


def available_models():
    return sorted(MODELS.keys())

