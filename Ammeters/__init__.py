# ammeters/__init__.py
# Single source of truth for emulator class registry.
# Add new ammeter classes here — all other files import from here.

from ammeters.greenlee_ammeter import GreenleeAmmeter
from ammeters.entes_ammeter    import EntesAmmeter
from ammeters.circutor_ammeter import CircutorAmmeter

EMULATOR_CLASSES = {
    "greenlee": GreenleeAmmeter,
    "entes":    EntesAmmeter,
    "circutor": CircutorAmmeter,
}

