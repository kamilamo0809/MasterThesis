# SPDX-FileCopyrightText: : 2023- The PyPSA-Eur Authors
#
# SPDX-License-Identifier: MIT


def add_nuclear_chp_constraints(network):
    # ratio between max heat output and max electric output
    nom_r = 2.2

    # backpressure limit
    c_b = 0.45

    # marginal loss for each additional generation of heat
    c_v = 0.12

    urban_central = network.buses.index[network.buses.carrier == "urban central heat"]
    urban_nodes = urban_central.str[: -len(" urban central heat")]
    
    model = network.model

    for node in urban_nodes:

        # Guarantees ISO fuel lines, i.e. fuel consumption p_b0 + p_g0 = constant along p_g1 + c_v p_b1 = constant
        #network.links.at[f"{node} nuclear CHP heat", "efficiency"] = (
        #    network.links.at[f"{node} nuclear CHP elec.", "efficiency"] / c_v
        #)
        heat_eff = float(network.links.at[f"{node} nuclear CHP heat", "efficiency"])
        elec_eff = float(network.links.at[f"{node} nuclear CHP elec.", "efficiency"])

        link_p = model.variables["Link-p"]
        link_p_nom = model.variables["Link-p_nom"]

        # Guarantees heat output and electric output nominal powers are proportional
        model.add_constraints(
            elec_eff * nom_r * link_p_nom.loc[f"{node} nuclear CHP elec."]
            - heat_eff * link_p_nom.loc[f"{node} nuclear CHP heat"]
            == 0,
            name=f"{node} heat-power output proportionality",
        )

        # Heat–power trade-off
        model.add_constraints(
            heat_eff * link_p.loc[:, f"{node} nuclear CHP heat"] <= 
            (link_p_nom.loc[f"{node} nuclear CHP elec."] - link_p.loc[:, f"{node} nuclear CHP elec."]) 
            * elec_eff / c_v,
            name=f"{node} heat-power trade-off",
        )

        # Backpressure constraint
        model.add_constraints(
            link_p.loc[:, f"{node} nuclear CHP heat"] * c_b * heat_eff
            - link_p.loc[:, f"{node} nuclear CHP elec."] * elec_eff
            <= 0,
            name=f"{node} back-pressure",
        )

        # Guarantees p_g1 +c_v p_b1 \leq p_g1_nom
        #model.add_constraints(
        #    link_p.loc[:, f"{node} nuclear CHP heat"] + link_p.loc[:, f"{node} nuclear CHP elec."] - link_p_nom.loc[f"{node} nuclear CHP elec."]
        #    <= 0,
        #    name=f"{node} top_iso_fuel_line",
        #)
"""
def add_nuclear_chp_constraints(network):
    # ratio between max heat output and max electric output
    nom_r = 2.2

    # backpressure limit
    c_b = 0.45

    # marginal loss for each additional generation of heat
    c_v = 0.2

    urban_central = network.buses.index[network.buses.carrier == "urban central heat"]
    urban_nodes = urban_central.str[: -len(" urban central heat")]
    
    model = network.model

    for node in urban_nodes:

        # Guarantees ISO fuel lines, i.e. fuel consumption p_b0 + p_g0 = constant along p_g1 + c_v p_b1 = constant
        #network.links.at[f"{node} nuclear CHP heat", "efficiency"] = (
        #    network.links.at[f"{node} nuclear CHP elec.", "efficiency"] / c_v
        #)
        heat_eff = float(network.links.at[f"{node} nuclear CHP heat", "efficiency"])
        elec_eff = float(network.links.at[f"{node} nuclear CHP elec.", "efficiency"])

        link_p1 = - model.variables["Link-p"]
        link_p_nom = model.variables["Link-p_nom"]

        # Guarantees heat output and electric output nominal powers are proportional
        model.add_constraints(
            elec_eff * nom_r * link_p_nom.loc[f"{node} nuclear CHP elec."]
            - heat_eff * link_p_nom.loc[f"{node} nuclear CHP heat"]
            == 0,
            name=f"{node} heat-power output proportionality",
        )

        # Heat–power trade-off
        model.add_constraints(
            link_p1.loc[:, f"{node} nuclear CHP heat"] == 
            (link_p_nom.loc[f"{node} nuclear CHP elec."] * elec_eff - link_p1.loc[:, f"{node} nuclear CHP elec."]) 
            / c_v,
            name=f"{node} heat-power trade-off",
        )

        # Backpressure constraint
        model.add_constraints(
            link_p1.loc[:, f"{node} nuclear CHP heat"] * c_b
            - link_p1.loc[:, f"{node} nuclear CHP elec."]
            <= 0,
            name=f"{node} back-pressure",
        )
"""


def custom_extra_functionality(n, snapshots, snakemake):
    """
    Add custom extra functionality constraints.
    """
    add_nuclear_chp_constraints(n)
