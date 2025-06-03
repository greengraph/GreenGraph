# Notation and Convention

## Mathematical Notation

## Diagrammatic Notation

Systems representing supply chains are beste understood when visualized using a well-defined diagrammatic notation. The `greengraph` package uses a notation formalized by Weinold in 2025. It defines the following elements, describing nodes and edges of the graph diagram:

| Image            | Type | Description       | Notes           |
|------------------|-------|------------|-----------------|
| ![](_media/legend/sector.svg) | node | sector $A$ | Squares represent sectors of the input-output (="sectoral system"). They are labeled using capital letters. |
| ![](_media/legend/process.svg) | node | process $1$ | Circles represent production processes of the life-cycle inventory (="process system"). They are labeled using numbers. |
| ![](_media/legend/burden.svg)| node | burden $\alpha$ | Diamonds represent environmental burdens or satellite extensions. They are labeled using lowercase Greek letters. |
| ![](_media/legend/flow_process.svg) | edge | process flow $a^P_{21}$ | Dashed lines represent flow information derived from the process system. |
| ![](_media/legend/flow_sector.svg) | edge | process flow $a^S_{BA}$ | Solid lines represent flow information derived from the sectoral system. |
| ![](_media/legend/flow_upstream.svg) | edge | upstream flow $c^U_{B1}$ | Red-colored lines represent flow from sectors to processes. [For historical reasons](https://doi.org/10.1016/j.ecolecon.2003.10.013), this is named _upstream flow_. |
| ![](_media/legend/flow_downstream.svg) | edge | downstream flow $c^D_{2A}$ | Blue-colored lines represent flow from  processes to sectors. [For historical reasons](https://doi.org/10.1016/j.ecolecon.2003.10.013), this is named _downstream flow_. |

Using this notation, the matrices underlying a simple example system can easily be reproduced. For example, the example system:

## Graph Flow Convention

Graph flow convention is chosen such that the direction of the flow allows for the simple construction of adjacency matrices.

| Image            | Node Flow  | Description       | Example Matrix           |
|------------------|-------|------------|-----------------|
| ![](_media/convention/A.svg) | `production`→ `production` | Physical or monetary flow from production node $B$ to $A$. | $\mathbf{B}$ |
| ![](_media/convention/B.svg) | `extension` → `production` | ⚠️ Production of the output of node $A$ is responsible for production of extension $\alpha$ (eg. =$A$ emits $\alpha$). | Squares represent sectors of the input-output (="sectoral system"). They are labeled using capital letters. |
| ![](_media/convention/H.svg) | `production` (sectoral) → `production` (process)  | Sector $A$ contains process $1$. | Squares represent sectors of the input-output (="sectoral system"). They are labeled using capital letters. |