# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT
"""
Creates plots for optimised power network topologies and regional generation,
storage and conversion capacities built.
"""

import logging

import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pypsa
from _helpers import configure_logging, rename_techs, retry, set_scenario_config
from plot_summary import preferred_order
from pypsa.plot import add_legend_circles, add_legend_lines, add_legend_patches

logger = logging.getLogger(__name__)


def rename_techs_tyndp(tech):
    tech = rename_techs(tech)
    if "heat pump" in tech or "resistive heater" in tech:
        return "power-to-heat"
    elif tech in ["H2 Electrolysis", "methanation", "H2 liquefaction"]:
        return "power-to-gas"
    elif tech == "H2":
        return "H2 storage"
    elif tech in ["NH3", "Haber-Bosch", "ammonia cracker", "ammonia store"]:
        return "ammonia"
    elif tech in ["OCGT", "CHP", "gas boiler", "H2 Fuel Cell"]:
        return "gas-to-power/heat"
    # elif "solar" in tech:
    #     return "solar"
    elif tech in ["Fischer-Tropsch", "methanolisation"]:
        return "power-to-liquid"
    elif "offshore wind" in tech:
        return "offshore wind"
    elif "CC" in tech or "sequestration" in tech:
        return "CCS"
    else:
        return tech


@retry
def plot_danish_annual_costs(n, pos, components=["links", "stores", "storage_units", "generators"]):
    import numpy as np
    tech_colors = snakemake.params.plotting["tech_colors"]

    costs = pd.Series(dtype=float)

    for comp in components:
        df_c = getattr(n, comp)
        if df_c.empty:
            continue

        # Filtrer til Danmark
        if "bus0" in df_c.columns:
            dk_mask = df_c["bus0"].str.startswith("DK") | df_c["bus1"].str.startswith("DK")
        elif "bus" in df_c.columns:
            dk_mask = df_c["bus"].str.startswith("DK")
        else:
            dk_mask = pd.Series(False, index=df_c.index)

        df_c = df_c[dk_mask].copy()
        if df_c.empty:
            continue

        df_c["nice_group"] = df_c.carrier.map(rename_techs_tyndp)

        attr = "e_nom_opt" if comp == "stores" else "p_nom_opt"
        lifetime = df_c.get("lifetime", 25).replace(np.inf, 60)
        df_c["annual_capex"] = df_c[attr] * df_c.capital_cost

        # Tidsseriedata
        if comp == "generators":
            p_t = n.generators_t.p[df_c.index]
        elif comp == "links":
            p_t = n.links_t.p1[df_c.index] * -1
        elif comp == "stores":
            p_t = n.stores_t.e[df_c.index]
        elif comp == "storage_units":
            p_t = n.storage_units_t.p[df_c.index]
        else:
            p_t = None

        # Marginalkostnad
        if p_t is not None:
            marginal_cost = (p_t.sum() * df_c["marginal_cost"]).groupby(df_c["nice_group"]).sum()
        else:
            marginal_cost = pd.Series(0.0, index=df_c["nice_group"].unique())

        # Summer årlig kapital + marginalkostnad per teknologi
        capex_grouped = df_c.groupby("nice_group")["annual_capex"].sum()
        total_cost = capex_grouped.add(marginal_cost, fill_value=0)

        costs = costs.add(total_cost, fill_value=0)

        logger.debug(f"{comp} total costs:\n{total_cost}")

    # Filtrer bort små verdier og sorter
    threshold = 1e6  # MEUR
    costs = costs[costs > threshold].sort_values(ascending=False) / 1e6  # MEUR/yr

    # Plot: én bar for Danmark, med teknologier stablet oppå hverandre
    bottom = 0
    for tech, value in costs.items():
        label = tech if tech not in seen_labels else None
        ax.bar(
            x=pos,
            height=value,
            bottom=bottom,
            width=0.3,
            color=tech_colors.get(tech, "gray"),
            label=label,
        )
        seen_labels.add(tech)
        bottom += value






if __name__ == "__main__":
    if "snakemake" not in globals():
        from _helpers import mock_snakemake

        snakemake = mock_snakemake(
            "plot_power_network",
            opts="lv1.0",
            clusters="50",
            ll="v1.0",
            sector_opts="3H-T-H-B-I-solar+p3-dist1-cb73.9ex0",
        )

    configure_logging(snakemake)
    set_scenario_config(snakemake)

    n11 = pypsa.Network(snakemake.input.network11)
    n13 = pypsa.Network(snakemake.input.network13)
    n21 = pypsa.Network(snakemake.input.network21)
    n23 = pypsa.Network(snakemake.input.network23)

    position11 = 0.83
    position13 = 1.17
    position21 = 1.83
    position23 = 2.17

    x = [position11, position13, position21, position23]

    fig, ax = plt.subplots(figsize=(12, 6.5))

    seen_labels = set()

    plot_danish_annual_costs(n11, position11)
    plot_danish_annual_costs(n13, position13)
    plot_danish_annual_costs(n21, position21)
    plot_danish_annual_costs(n23, position23)

    # --- Add Labels ---
    # Common labels for grouped bars
    group_labels = ["Autarky", "Connected"]
    group_positions = [(x[0] + x[1]) / 2, (x[2] + x[3]) / 2]

    # Set grouped labels at midpoint
    for label, pos in zip(group_labels, group_positions):
        if label:  # Avoid empty labels
            ax.text(pos, - 2500, label, ha = 'center', va = 'top', fontsize = 14)

    bbbl = ['Transport', 'EVs only', 'Transport', 'EVs only',]
    import seaborn as sns
    fig.patch.set_facecolor("white")  # Setter figurbakgrunn
    ax.set_facecolor("white")         # Setter plotområdet hvitt

    # Forbedret utseende
    ax.set_xticks(x)
    ax.set_xticklabels(bbbl, rotation = 0, ha = 'center', fontsize = 12)
    ax.xaxis.set_tick_params(pad = 10)  # Moves labels further away from axis
    plt.grid(True, linestyle = '--', axis = 'y')

    ax.set_ylabel("Total annual costs (MEUR/year)")
    #ax.set_title("Total investment per technology")
    plt.legend(loc = 'center left', bbox_to_anchor = (1.02, 0.5),  # Push legend outside the axes
            borderaxespad = 0., frameon = False, labelspacing = 1)
    ax.grid(True, axis="y", color = "lightgrey")
    fig.tight_layout()
    
    fig.savefig(snakemake.output.bar_dk_eps, bbox_inches = "tight")
    fig.savefig(snakemake.output.bar_dk, bbox_inches="tight")
    plt.close(fig)

