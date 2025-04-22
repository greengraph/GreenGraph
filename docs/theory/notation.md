# Notation and Diagrams

Systems representing supply chains are beste understood when visualized using a well-defined diagrammatic notation. The `greengraph` package uses a notation formalized by Weinold in 2025. It defines the following elements, describing nodes and edges of the graph diagram:

| Image            | Type | Description       | Notes           |
|------------------|-------|------------|-----------------|
| <img src="../../_media/legend/sector.svg" width="100"> | node | sector $A$ | Squares represent sectors of the input-output (="sectoral system"). They are labeled using capital letters. |
| <img src="../../_media/legend/process.svg" width="100"> | node | process $1$ | Circles represent production processes of the life-cycle inventory (="process system"). They are labeled using numbers. |
| <img src="../../_media/legend/burden.svg" width="100"> | node | burden $\alpha$ | Diamonds represent environmental burdens or satellite extensions. They are labeled using lowercase Greek letters. |
| <img src="../../_media/legend/flow_process.svg" width="100"> | edge | process flow $a^P_{21}$ | Dashed lines represent flow information derived from the process system. |
| <img src="../../_media/legend/flow_sector.svg" width="100"> | edge | process flow $a^S_{BA}$ | Solid lines represent flow information derived from the sectoral system. |
| <img src="../../_media/legend/flow_upstream.svg" width="100"> | edge | upstream flow $c^U_{B1}$ | Red-colored lines represent flow from sectors to processes. [For historical reasons](https://doi.org/10.1016/j.ecolecon.2003.10.013), this is named _upstream flow_. |
| <img src="../../_media/legend/flow_downstream.svg" width="100"> | edge | downstream flow $c^D_{2A}$ | Blue-colored lines represent flow from  processes to sectors. [For historical reasons](https://doi.org/10.1016/j.ecolecon.2003.10.013), this is named _downstream flow_. |

Using this notation, the matrices underlying a simple example system can easily be reproduced. For example, the example system: