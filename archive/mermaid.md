``` mermaid
flowchart LR
 subgraph Sectors["Sectors"]
        A["A"]
  end
 subgraph s1["Satellites"]
        n2["β"]
        n3["ɣ"]
  end
 subgraph s3["Impacts"]
        n4["I₁"]
  end
    n2 --> n4
    n3 --> n4
    A --> n3
    A --> n2
    A@{ shape: rect}
    n2@{ shape: diam}
    n3@{ shape: diam}
    n4@{ shape: tri}
    style n2 stroke:#00C853
    style n3 stroke:#00C853
    style n4 stroke:#D50000
    style s1 fill:transparent
    style Sectors fill:transparent
    style s3 fill:transparent
```