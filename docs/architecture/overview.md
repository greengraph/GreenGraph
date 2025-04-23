# `greengraph` Structure

!!! note
    For a complete legend of the diagrammatic notation used in the figures of this section, see the [notation section](../theory/notation.md).

Simple example system consisting of two sectors $(A,B)$ and two processes $(1,2)$, with one burden $(\alpha)$. Illustrated is the `greengraph` concept of a __system__: nodes which _belong together_. This same example system can also be rendered in this way:

<div align="center">
    <img src="../../_media/terminology.svg" width="600">
</div>

In GreenGraph, all data related to the system is stored as a graph.


\begin{align}
\mathbf{A}_S &= \begin{bmatrix}
a^S_{AA} & a^S_{AB} \\
a^S_{BA} & a^S_{BB}
\end{bmatrix} \\
\mathbf{B}_S &= \begin{bmatrix}
b^S_{A \gamma} & b^S_{B \gamma}
\end{bmatrix}
\end{align}

and 

\begin{align}
\mathbf{A}_P &= \begin{bmatrix}
a^P_{11}=0 & a^P_{12} \\
a^P_{21} & a^P_{22}=0
\end{bmatrix} \\
\mathbf{B}_P &= \begin{bmatrix}
b^P_{1 \alpha} & b^P_{2 \alpha} \\
b^P_{1 \beta} & b^P_{2 \beta}
\end{bmatrix}
\end{align}

the connection between the two systems can be represented through an _upstream cut-off matrix_ $\mathbf{C}^U$:

\begin{equation}
\mathbf{C}^U = \begin{bmatrix}
c^U_{A1}=0 & c^U_{A2} \neq 0 \\
c^U_{B1}=0 & c^U_{B2}=0
\end{bmatrix}
\end{equation}

The relation between the two systems can be expressed through a _concordance matrix_ $\mathbf{H}$, which is defined as:

\begin{equation}
h_{ij} = \begin{cases}
1 & \text{sector $i$ contains process $j$} \\
0 & \text{otherwise}
\end{cases}
\end{equation}

\begin{equation}
\mathbf{H} = \begin{bmatrix}
h_{A1}=1 & h_{A2}=0 \\
h_{B1}=0 & h_{B2}=1
\end{bmatrix}
\end{equation}

