def euro(value: float) -> str:
    return (
        f"{value:,.2f}\u00a0€"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def signed_euro(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{euro(value)}"


def movement_type_from_amount(amount: float) -> str:
    """Classifica l'importo: zero non conta come uscita."""
    if amount > 0:
        return "Entrata"

    if amount < 0:
        return "Uscita"

    return "Entrata"
