from mxlpy import Model

from mxlbricks import names as n
from mxlbricks.utils import (
    default_kf,
    default_name,
)


def _rate_cyclic_electron_flow(
    Pox: float,
    Fdred: float,
    kcyc: float,
) -> float:
    return kcyc * Fdred**2 * Pox


def add_cyclic_electron_flow(
    model: Model,
    *,
    rxn: str | None = None,
    kf: str | None = None,
) -> Model:
    rxn = default_name(rxn, n.cyclic_electron_flow)

    model.add_reaction(
        name=rxn,
        fn=_rate_cyclic_electron_flow,
        stoichiometry={
            n.pq_ox(): -1,
            n.fd_ox(): 2,
        },
        args=[
            n.pq_ox(),
            n.fd_red(),
            default_kf(model, rxn=rxn, par=kf, value=1.0),
        ],
    )
    return model
